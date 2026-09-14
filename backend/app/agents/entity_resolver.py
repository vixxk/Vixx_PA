"""
Entity Resolver & Fuzzy Matcher
===============================
Resolves user mentions of projects, dates, amounts, and tasks against the
actual database workspace context. Eliminates the need for spoon-feeding.
"""

import re
import dateutil.parser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

def resolve_project_from_text(
    text: str, 
    workspace_projects: Optional[List[Dict[str, Any]]] = None,
    active_context_title: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Intelligently matches a project from user query against workspace projects.
    Supports exact, case-insensitive, word-boundary, and prefix matching.
    """
    if not workspace_projects:
        return None

    text_lower = text.lower()

    # 1. Exact match against full project title
    for p in workspace_projects:
        p_title = p.get("title", "").strip()
        if not p_title:
            continue
        p_title_lower = p_title.lower()
        
        # Word boundary match in text: e.g. "for hyrego add..." matches "Hyrego"
        pattern = rf"\b{re.escape(p_title_lower)}\b"
        if re.search(pattern, text_lower):
            return p

    # 2. Match after prepositions: "for X", "to X", "in X", "on X", "project X"
    prep_match = re.search(r'(?:for|to|in|on|project|workspace)\s+([a-zA-Z0-9_\-]+)', text_lower)
    if prep_match:
        cand = prep_match.group(1).strip()
        for p in workspace_projects:
            p_title = p.get("title", "").strip().lower()
            if cand == p_title or cand in p_title or p_title.startswith(cand):
                return p

    # 3. Substring match
    for p in workspace_projects:
        p_title = p.get("title", "").strip().lower()
        if p_title and p_title in text_lower:
            return p

    # 4. If user says "this project", "current project", "it", and active context exists
    if any(kw in text_lower for kw in ["this project", "the project", "current project", "for this"]):
        if active_context_title:
            for p in workspace_projects:
                if p.get("title", "").lower() == active_context_title.lower():
                    return p
        if len(workspace_projects) == 1:
            return workspace_projects[0]

    return None


def parse_amount_from_text(text: str) -> Optional[float]:
    """
    Extracts numerical payment or budget amount from text.
    Handles '7000', '7k', 'Rs 7000', '7,000.50', '50k'.
    """
    text_lower = text.lower()
    
    # Check '7k' or '50k'
    k_match = re.search(r'\b([0-9]+(?:\.[0-9]+)?)\s*k\b', text_lower)
    if k_match:
        try:
            return float(k_match.group(1)) * 1000.0
        except ValueError:
            pass

    # Patterns like "add 7000", "7000 payment", "payment of 7000", "rs 7000"
    matches = re.findall(r'(?:(?:rs\.?|inr|₹|\$)\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?))|(?:(?:add|payment|amount|paid|value|cost|budget|for|of)\s+([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?))|(?:\b([0-9]{3,7})\b)', text_lower)
    for m in matches:
        val_str = m[0] or m[1] or m[2]
        if val_str:
            clean = val_str.replace(',', '')
            try:
                val = float(clean)
                # Filter out years like 2024, 2025, 2026 if preceded by year context
                if val in [2024, 2025, 2026] and ("year" in text_lower or re.search(rf'\b(?:in|of)\s+{int(val)}\b', text_lower)):
                    continue
                return val
            except ValueError:
                continue

    return None


def parse_date_from_text(text: str, reference_dt: Optional[datetime] = None) -> Optional[str]:
    """
    Parses dates like '7th june', 'tomorrow', '2024-06-07', 'yesterday'.
    Returns ISO format date string (YYYY-MM-DD).
    """
    ref_dt = reference_dt or datetime.now()
    text_lower = text.lower()

    if "today" in text_lower:
        return ref_dt.strftime("%Y-%m-%d")
    if "tomorrow" in text_lower:
        return (ref_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    if "yesterday" in text_lower:
        return (ref_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    # Match patterns like "7th june", "7 june", "june 7th", "june 7"
    date_match = re.search(r'\b([0-9]{1,2})(?:st|nd|rd|th)?\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s+([0-9]{4}))?\b', text_lower)
    if date_match:
        day = int(date_match.group(1))
        month_str = date_match.group(2)
        year = int(date_match.group(3)) if date_match.group(3) else ref_dt.year
        try:
            parsed = dateutil.parser.parse(f"{day} {month_str} {year}")
            return parsed.strftime("%Y-%m-%d")
        except Exception:
            pass

    month_first_match = re.search(r'\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+([0-9]{1,2})(?:st|nd|rd|th)?(?:\s+([0-9]{4}))?\b', text_lower)
    if month_first_match:
        month_str = month_first_match.group(1)
        day = int(month_first_match.group(2))
        year = int(month_first_match.group(3)) if month_first_match.group(3) else ref_dt.year
        try:
            parsed = dateutil.parser.parse(f"{month_str} {day} {year}")
            return parsed.strftime("%Y-%m-%d")
        except Exception:
            pass

    # ISO date match YYYY-MM-DD
    iso_match = re.search(r'\b([0-9]{4}-[0-9]{2}-[0-9]{2})\b', text)
    if iso_match:
        return iso_match.group(1)

    return None


def parse_update_amounts(text: str):
    """
    Parses expressions like:
    - 'change 7000 payment to 8500' -> (7000.0, 8500.0)
    - 'change payment from 7000 to 8500' -> (7000.0, 8500.0)
    - 'update payment to 8500' -> (None, 8500.0)
    Returns (old_amount, new_amount).
    """
    text_lower = text.lower()
    from_to = re.search(r'(?:from\s+)?(?:rs\.?|inr|₹|\$)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?|[0-9]+k)\s*(?:payment\s+)?(?:to|->)\s*(?:rs\.?|inr|₹|\$)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?|[0-9]+k)', text_lower)
    if from_to:
        v1_str, v2_str = from_to.group(1), from_to.group(2)
        try:
            v1 = float(v1_str.replace('k', '')) * 1000 if 'k' in v1_str else float(v1_str.replace(',', ''))
            v2 = float(v2_str.replace('k', '')) * 1000 if 'k' in v2_str else float(v2_str.replace(',', ''))
            return v1, v2
        except Exception:
            pass
    
    to_match = re.search(r'(?:to|set to|as)\s+(?:rs\.?|inr|₹|\$)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?|[0-9]+k)', text_lower)
    if to_match:
        v2_str = to_match.group(1)
        try:
            v2 = float(v2_str.replace('k', '')) * 1000 if 'k' in v2_str else float(v2_str.replace(',', ''))
            return None, v2
        except Exception:
            pass

    return None, None


def parse_rename_pattern(text: str):
    """
    Parses expressions like:
    - 'rename project Hyrego to Hyrego v2' -> ('Hyrego', 'Hyrego v2')
    - 'rename task finish auth to complete oauth flow' -> ('finish auth', 'complete oauth flow')
    - 'change name of X to Y' -> ('X', 'Y')
    Returns (old_name, new_name).
    """
    patterns = [
        r'rename\s+(?:project|task|milestone|item|todo)?\s*[\'"]?([^\'"]+?)[\'"]?\s+to\s+[\'"]?([^\'"]+?)[\'"]?$',
        r'change\s+(?:the\s+)?name\s+of\s+[\'"]?([^\'"]+?)[\'"]?\s+to\s+[\'"]?([^\'"]+?)[\'"]?$',
        r'change\s+[\'"]?([^\'"]+?)[\'"]?\s+to\s+[\'"]?([^\'"]+?)[\'"]?$',
    ]
    for p in patterns:
        m = re.search(p, text.strip(), re.IGNORECASE)
        if m:
            old_n = m.group(1).strip()
            new_n = m.group(2).strip()
            for prefix in ["project ", "task ", "milestone ", "todo "]:
                if old_n.lower().startswith(prefix):
                    old_n = old_n[len(prefix):].strip()
            return old_n, new_n
    return None, None
