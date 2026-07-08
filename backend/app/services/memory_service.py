"""
Memory Service
==============
Manages persistent conversation memory with three tiers:
1. Session Memory  — full messages within current session (DB-backed)
2. Entity Memory   — facts learned about projects/clients across sessions
3. Long-term Memory — compressed session summaries for cross-session recall

Replaces the volatile in-memory session_store dict.
"""

import uuid as uuid_mod
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func

from app.models.conversation_log import ConversationLog
from app.models.entity_memory import EntityMemory
from app.models.session_summary import SessionSummary
from app.models.session_state import SessionState
import logging

logger = logging.getLogger(__name__)

# In-memory cache for active sessions (lightweight — only metadata, not full history)
_active_sessions: Dict[str, Dict[str, Any]] = {}


def get_or_create_session(user_id: UUID, session_id_str: Optional[str] = None) -> Dict[str, Any]:
    """Get or create a session metadata entry for a user and session ID. Session ID persists until reset."""
    if not session_id_str:
        session_id_str = "default"
    
    try:
        session_id = UUID(session_id_str)
    except (ValueError, TypeError):
        # Generate a stable UUID based on user_id and session_id_str so it persists across restarts
        session_id = uuid_mod.uuid5(user_id, session_id_str)
        
    cache_key = f"{user_id}_{session_id}"
    if cache_key not in _active_sessions:
        _active_sessions[cache_key] = {
            "session_id": session_id,
            "last_project": None,
            "pending_state": None,
            "pending_delete_action": None,
            "message_count": 0,
        }
    return _active_sessions[cache_key]


def reset_session(user_id: UUID, session_id_str: Optional[str] = None):
    """Start a new session for a user."""
    if not session_id_str:
        session_id_str = "default"
    try:
        session_id = UUID(session_id_str)
    except (ValueError, TypeError):
        session_id = uuid_mod.uuid5(user_id, session_id_str)
        
    cache_key = f"{user_id}_{session_id}"
    if cache_key in _active_sessions:
        del _active_sessions[cache_key]


async def save_session_state(db: AsyncSession, user_id: UUID, session_id: UUID, state: dict):
    """Persist conversation state to database."""
    try:
        # Check if it already exists
        stmt = select(SessionState).filter(SessionState.session_id == session_id)
        res = await db.execute(stmt)
        sess = res.scalars().first()
        
        # Strip out non-JSON serializable keys or complex objects if any
        serialized_state = {}
        for k, v in state.items():
            try:
                import json
                json.dumps({k: v})
                serialized_state[k] = v
            except Exception:
                pass
                
        if sess:
            sess.state = serialized_state
        else:
            sess = SessionState(session_id=session_id, user_id=user_id, state=serialized_state)
            db.add(sess)
        await db.flush()
    except Exception as e:
        logger.error(f"Error saving session state: {e}")


async def get_session_state(db: AsyncSession, user_id: UUID, session_id: UUID) -> Optional[dict]:
    """Retrieve persisted conversation state from database."""
    try:
        stmt = select(SessionState).filter(SessionState.session_id == session_id)
        res = await db.execute(stmt)
        sess = res.scalars().first()
        if sess:
            return sess.state
    except Exception as e:
        logger.error(f"Error loading session state: {e}")
    return None


async def delete_session_state(db: AsyncSession, user_id: UUID, session_id: UUID):
    """Delete persisted conversation state from database."""
    try:
        stmt = select(SessionState).filter(SessionState.session_id == session_id)
        res = await db.execute(stmt)
        sess = res.scalars().first()
        if sess:
            await db.delete(sess)
            await db.flush()
    except Exception as e:
        logger.error(f"Error deleting session state: {e}")


async def save_message(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    role: str,
    content: str,
    intent: Optional[str] = None,
    entities: Optional[dict] = None,
):
    """Save a conversation message to persistent storage."""
    log = ConversationLog(
        user_id=user_id,
        session_id=session_id,
        role=role,
        content=content,
        intent=intent,
        entities=entities,
    )
    db.add(log)
    # Don't commit here — let the caller's transaction handle it
    await db.flush()


async def get_session_history(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    limit: int = 20,
) -> List[Dict[str, str]]:
    """Retrieve recent messages from the current session."""
    stmt = (
        select(ConversationLog)
        .filter(
            ConversationLog.user_id == user_id,
            ConversationLog.session_id == session_id,
            ConversationLog.role.in_(["user", "assistant"]),
        )
        .order_by(desc(ConversationLog.created_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()

    # Reverse to get chronological order
    logs.reverse()
    return [{"role": log.role, "content": log.content} for log in logs]


async def get_recent_history(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 20,
) -> List[Dict[str, str]]:
    """Retrieve the most recent messages regardless of session (for context continuity)."""
    stmt = (
        select(ConversationLog)
        .filter(
            ConversationLog.user_id == user_id,
            ConversationLog.role.in_(["user", "assistant"]),
        )
        .order_by(desc(ConversationLog.created_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()
    logs.reverse()
    return [{"role": log.role, "content": log.content} for log in logs]


async def get_relevant_context(
    db: AsyncSession,
    user_id: UUID,
    query: str,
    limit: int = 6,
) -> List[Dict[str, str]]:
    """
    Retrieve messages relevant to a query using keyword matching.
    This is a simple keyword-based retrieval; can be upgraded to vector search later.
    """
    # Extract significant words from query (skip very short words)
    keywords = [w.lower() for w in query.split() if len(w) > 3]

    if not keywords:
        return await get_recent_history(db, user_id, limit)

    # Search for messages containing any keyword
    # Use a simple OR filter with ilike
    from sqlalchemy import or_
    filters = [ConversationLog.content.ilike(f"%{kw}%") for kw in keywords[:5]]

    stmt = (
        select(ConversationLog)
        .filter(
            ConversationLog.user_id == user_id,
            ConversationLog.role.in_(["user", "assistant"]),
            or_(*filters),
        )
        .order_by(desc(ConversationLog.created_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()
    logs.reverse()
    return [{"role": log.role, "content": log.content} for log in logs]


async def store_entity_fact(
    db: AsyncSession,
    user_id: UUID,
    entity_type: str,
    entity_name: str,
    fact: str,
    entity_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
):
    """Store a learned fact about an entity."""
    # Check for duplicate facts
    stmt = select(EntityMemory).filter(
        EntityMemory.user_id == user_id,
        EntityMemory.entity_type == entity_type,
        EntityMemory.entity_name == entity_name,
        EntityMemory.fact == fact,
    )
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        existing.last_accessed_at = datetime.now(timezone.utc)
        await db.flush()
        return existing

    mem = EntityMemory(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        fact=fact,
        source_session_id=session_id,
    )
    db.add(mem)
    await db.flush()
    return mem


async def recall_entity_facts(
    db: AsyncSession,
    user_id: UUID,
    entity_type: Optional[str] = None,
    entity_name: Optional[str] = None,
    limit: int = 10,
) -> List[str]:
    """Recall stored facts about an entity."""
    stmt = select(EntityMemory).filter(EntityMemory.user_id == user_id)
    if entity_type:
        stmt = stmt.filter(EntityMemory.entity_type == entity_type)
    if entity_name:
        stmt = stmt.filter(EntityMemory.entity_name.ilike(f"%{entity_name}%"))
    stmt = stmt.order_by(desc(EntityMemory.last_accessed_at)).limit(limit)

    result = await db.execute(stmt)
    memories = result.scalars().all()

    # Update last_accessed_at
    for mem in memories:
        mem.last_accessed_at = datetime.now(timezone.utc)
    if memories:
        await db.flush()

    return [f"[{m.entity_type}:{m.entity_name}] {m.fact}" for m in memories]


async def summarize_and_archive_session(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
):
    """
    Summarize a session's conversation and store it as a compressed summary.
    Called when a session gets too long or when the user starts a new session.
    """
    # Get all messages from this session
    stmt = (
        select(ConversationLog)
        .filter(
            ConversationLog.user_id == user_id,
            ConversationLog.session_id == session_id,
        )
        .order_by(ConversationLog.created_at)
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()

    if len(logs) < 4:
        return  # Too few messages to summarize

    # Build a simple summary from the messages
    message_count = len(logs)
    intents_used = set()
    entities_mentioned = set()

    for log in logs:
        if log.intent:
            intents_used.add(log.intent)
        if log.entities:
            for val in log.entities.values():
                if val:
                    entities_mentioned.add(str(val))

    # Create a text summary from the conversation
    try:
        from app.utils.llm import get_llm
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = get_llm()
        conv_text = "\n".join([f"{l.role}: {l.content[:200]}" for l in logs[-20:]])
        prompt = (
            "Summarize this conversation in 2-3 sentences. Focus on what was discussed, "
            "what actions were taken, and any important context:\n\n" + conv_text
        )
        response = await llm.ainvoke([
            SystemMessage(content="You are a concise summarizer."),
            HumanMessage(content=prompt),
        ])
        summary_text = response.content.strip()
    except Exception:
        # Fallback: basic summary
        actions = ", ".join(intents_used) if intents_used else "general conversation"
        summary_text = f"Session with {message_count} messages. Actions: {actions}."

    summary = SessionSummary(
        user_id=user_id,
        session_id=session_id,
        summary=summary_text,
        key_entities=list(entities_mentioned) if entities_mentioned else None,
        key_actions=list(intents_used) if intents_used else None,
        message_count=message_count,
    )
    db.add(summary)
    await db.flush()
    return summary


async def get_session_count(db: AsyncSession, user_id: UUID, session_id: UUID) -> int:
    """Get the number of messages in a session."""
    stmt = select(func.count(ConversationLog.id)).filter(
        ConversationLog.user_id == user_id,
        ConversationLog.session_id == session_id,
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def rename_session(db: AsyncSession, user_id: UUID, session_id: UUID, title: str):
    """Rename a conversation session by upserting a system-level metadata record."""
    stmt = select(ConversationLog).filter(
        ConversationLog.user_id == user_id,
        ConversationLog.session_id == session_id,
        ConversationLog.role == "system",
        ConversationLog.intent == "session_title"
    )
    result = await db.execute(stmt)
    log = result.scalars().first()
    if log:
        log.content = title
    else:
        log = ConversationLog(
            user_id=user_id,
            session_id=session_id,
            role="system",
            intent="session_title",
            content=title
        )
        db.add(log)
    await db.commit()


async def delete_session(db: AsyncSession, user_id: UUID, session_id: UUID):
    """Delete all logs and metadata associated with a session ID."""
    from app.models.session_summary import SessionSummary
    from app.models.session_state import SessionState
    
    # Delete logs
    log_stmt = select(ConversationLog).filter(
        ConversationLog.user_id == user_id,
        ConversationLog.session_id == session_id
    )
    logs = (await db.execute(log_stmt)).scalars().all()
    for log in logs:
        await db.delete(log)
        
    # Delete summary
    sum_stmt = select(SessionSummary).filter(
        SessionSummary.user_id == user_id,
        SessionSummary.session_id == session_id
    )
    sums = (await db.execute(sum_stmt)).scalars().all()
    for s in sums:
        await db.delete(s)
        
    # Delete state
    state_stmt = select(SessionState).filter(
        SessionState.user_id == user_id,
        SessionState.session_id == session_id
    )
    states = (await db.execute(state_stmt)).scalars().all()
    for st in states:
        await db.delete(st)
        
    await db.commit()


async def get_all_sessions(db: AsyncSession, user_id: UUID) -> List[Dict[str, Any]]:
    """Retrieve all user sessions grouped by session ID, ordered by creation time."""
    stmt = (
        select(ConversationLog)
        .filter(ConversationLog.user_id == user_id)
        .order_by(ConversationLog.created_at.asc())
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    sessions_dict = {}
    for log in logs:
        s_id = str(log.session_id)
        if s_id not in sessions_dict:
            sessions_dict[s_id] = {
                "id": s_id,
                "title": "New Session",
                "messages": [],
                "createdAt": log.created_at.isoformat() if log.created_at else datetime.now().isoformat()
            }
            
        if log.role == "system" and log.intent == "session_title":
            sessions_dict[s_id]["title"] = log.content
        else:
            sessions_dict[s_id]["messages"].append({
                "id": str(log.id),
                "sender": log.role,
                "text": log.content,
                "type": "normal",
                "reasoningSteps": log.entities.get("reasoningSteps") if log.entities and isinstance(log.entities, dict) else []
            })
            
    # Return as list sorted by creation time or last activity (e.g. descending)
    sessions_list = list(sessions_dict.values())
    sessions_list.sort(key=lambda x: x["createdAt"], reverse=True)
    return sessions_list
