"""
Entity Resolution Service
=========================
Fuzzy matching + disambiguation for projects, tasks, and other entities.
Replaces the naive string-containment matching in ai.py with scored matching,
multi-entity resolution, and exclusion pattern support.
"""

from difflib import SequenceMatcher
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

# Suffixes/prefixes to strip when comparing entity names
STRIP_SUFFIXES = [" project", " workspace", " app", " application", " site", " website"]
STRIP_PREFIXES = ["the ", "my ", "our "]

MATCH_THRESHOLD = 0.55  # Minimum fuzzy score to consider a match


def normalize_name(name: str) -> str:
    """Normalize an entity name for comparison."""
    n = name.lower().strip()
    for prefix in STRIP_PREFIXES:
        if n.startswith(prefix):
            n = n[len(prefix):]
    for suffix in STRIP_SUFFIXES:
        if n.endswith(suffix):
            n = n[:-len(suffix)]
    return n.strip()


def fuzzy_score(query: str, candidate: str) -> float:
    """
    Return a similarity score between 0 and 1.
    Uses a tiered matching approach: exact > normalized-exact > prefix > substring > fuzzy.
    """
    q_raw = query.lower().strip()
    c_raw = candidate.lower().strip()

    # Raw exact match
    if q_raw == c_raw:
        return 1.0

    q = normalize_name(query)
    c = normalize_name(candidate)

    # Normalized exact match
    if q == c:
        return 0.99

    # Exact prefix match (query is a prefix of candidate or vice versa)
    if c.startswith(q) or q.startswith(c):
        # Score by how much of the longer string is covered
        coverage = min(len(q), len(c)) / max(len(q), len(c))
        return 0.90 + (coverage * 0.08)

    # Substring match
    if q in c:
        return 0.80 + (len(q) / len(c)) * 0.10
    if c in q:
        return 0.75 + (len(c) / len(q)) * 0.10

    # Word overlap: check if all words in query appear in candidate
    q_words = set(q.split())
    c_words = set(c.split())
    if q_words and q_words.issubset(c_words):
        return 0.85
    if c_words and c_words.issubset(q_words):
        return 0.80

    # Fuzzy match using SequenceMatcher
    return SequenceMatcher(None, q, c).ratio()


async def resolve_project(
    db: AsyncSession,
    user_id: UUID,
    query: str,
    exclude_names: Optional[List[str]] = None,
) -> Optional["Project"]:
    """
    Find the single best-matching project for a query.
    
    Returns:
        The best matching Project, or None if no match found.
    """
    from app.models.project import Project

    stmt = select(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    projects = result.scalars().all()

    if not projects:
        return None

    return _best_match(query, projects, key=lambda p: p.title, exclude_names=exclude_names)


async def resolve_projects_multi(
    db: AsyncSession,
    user_id: UUID,
    query: str,
    exclude_names: Optional[List[str]] = None,
) -> List["Project"]:
    """
    Find ALL projects matching a query (for batch operations like 'delete all projects named X').
    Respects exclusion patterns.
    
    Returns:
        List of matching Projects (may be empty).
    """
    from app.models.project import Project

    stmt = select(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    projects = result.scalars().all()

    if not projects:
        return []

    matches = []
    exclude_normalized = [normalize_name(n) for n in (exclude_names or [])]

    for project in projects:
        score = fuzzy_score(query, project.title)
        if score >= MATCH_THRESHOLD:
            # Check exclusion list
            p_normalized = normalize_name(project.title)
            if any(fuzzy_score(exc, project.title) >= 0.85 for exc in (exclude_names or [])):
                logger.info(f"Entity resolver: excluding '{project.title}' from batch operation")
                continue
            matches.append(project)

    return matches


async def resolve_task(
    db: AsyncSession,
    project_ids: List[UUID],
    query: str,
) -> Optional["Todo"]:
    """Find the best matching task/todo by title."""
    from app.models.todo import Todo

    stmt = select(Todo).filter(Todo.project_id.in_(project_ids))
    result = await db.execute(stmt)
    todos = result.scalars().all()

    if not todos:
        return None

    return _best_match(query, todos, key=lambda t: t.title)


async def resolve_pending_item(
    db: AsyncSession,
    project_ids: List[UUID],
    query: str,
) -> Optional["PendingThing"]:
    """Find the best matching pending item by title."""
    from app.models.pending_thing import PendingThing

    stmt = select(PendingThing).filter(PendingThing.project_id.in_(project_ids))
    result = await db.execute(stmt)
    items = result.scalars().all()

    if not items:
        return None

    return _best_match(query, items, key=lambda p: p.title)


async def resolve_project_from_context(
    db: AsyncSession,
    user_id: UUID,
    raw_input: str,
    extracted_title: Optional[str] = None,
    session_data: Optional[dict] = None,
) -> Optional["Project"]:
    """
    Smart project resolution that tries multiple strategies:
    1. Use extracted title (from LLM extraction)
    2. Search raw_input for known project names
    3. Use last_project from session context
    4. If user has only 1 project, use that
    """
    from app.models.project import Project

    stmt = select(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    projects = result.scalars().all()

    if not projects:
        return None

    # Strategy 1: Use extracted title
    if extracted_title and extracted_title.lower() not in ["all", "list", "projects", "none"]:
        match = _best_match(extracted_title, projects, key=lambda p: p.title)
        if match:
            return match

    # Strategy 2: Scan raw_input for project names
    raw_lower = raw_input.lower()
    best_project = None
    best_score = 0
    for p in projects:
        # Check if any significant word from the project title appears in the input
        p_normalized = normalize_name(p.title)
        score = 0

        if p.title.lower() in raw_lower:
            score = 0.95
        elif p_normalized in raw_lower:
            score = 0.90
        else:
            # Check word overlap
            p_words = [w for w in p_normalized.split() if len(w) > 2]
            input_words = raw_lower.split()
            if p_words:
                overlap = sum(1 for w in p_words if w in input_words)
                score = overlap / len(p_words) * 0.80

        if score > best_score and score >= 0.5:
            best_score = score
            best_project = p

    if best_project:
        return best_project

    # Strategy 3: Use session context (last mentioned project)
    if session_data:
        last_project = session_data.get("last_project")
        if last_project and last_project.get("id"):
            for p in projects:
                if str(p.id) == last_project["id"]:
                    return p

    # Strategy 4: If only 1 project exists, use it
    if len(projects) == 1:
        return projects[0]

    return None


def _best_match(query: str, candidates: list, key=lambda x: x, exclude_names: Optional[List[str]] = None):
    """
    Find the best matching candidate using fuzzy scoring.
    
    Args:
        query: The search string
        candidates: List of objects to match against
        key: Function to extract the name string from each candidate
        exclude_names: Names to exclude from results
    
    Returns:
        The best matching candidate, or None if no good match found.
    """
    if not candidates:
        return None

    scored = []
    for candidate in candidates:
        name = key(candidate)
        score = fuzzy_score(query, name)

        # Check exclusion
        if exclude_names:
            excluded = False
            for exc in exclude_names:
                if fuzzy_score(exc, name) >= 0.85:
                    excluded = True
                    break
            if excluded:
                continue

        if score >= MATCH_THRESHOLD:
            scored.append((score, candidate))

    if not scored:
        return None

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]
