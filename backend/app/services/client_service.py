"""
Client Service
==============
Handles Client CRUD operations and calculates client engagement reliability scores.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
import uuid as uuid_mod
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.client import Client
from app.models.project import Project
from app.models.payment import Payment
from app.services.entity_resolver import fuzzy_score
import logging

logger = logging.getLogger(__name__)


async def list_clients(db: AsyncSession, user_id: UUID) -> str:
    """Lists all clients with their engagement scores and company details."""
    stmt = select(Client).filter(Client.user_id == user_id).order_by(Client.name.asc())
    clients = (await db.execute(stmt)).scalars().all()
    if not clients:
        return "No clients found. You can add one by saying: 'add client John Doe from Acme Inc'."
        
    msg = "### 💼 Your Clients:\n\n"
    for c in clients:
        co = f" ({c.company})" if c.company else ""
        msg += f"- **{c.name}**{co} — Priority Score: **{c.priority_score}/100**\n"
        if c.email or c.phone:
            msg += f"  _Contact: {c.email or '-'} | {c.phone or '-'}_\n"
        if c.notes:
            msg += f"  _{c.notes}_\n"
    return msg


async def create_client(db: AsyncSession, user_id: UUID, client_data: dict) -> str:
    """Creates a new client."""
    name = client_data.get("name")
    if not name:
        return "Please specify a client name."
        
    # Check if duplicate exists
    stmt = select(Client).filter(Client.user_id == user_id, Client.name.ilike(name))
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        return f"Client '{name}' already exists."

    new_client = Client(
        user_id=user_id,
        name=name,
        email=client_data.get("email"),
        phone=client_data.get("phone"),
        company=client_data.get("company"),
        notes=client_data.get("notes"),
        priority_score=client_data.get("priority_score") or 70
    )
    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)
    return f"Successfully registered client **{new_client.name}**."


async def update_client(db: AsyncSession, user_id: UUID, client_data: dict) -> str:
    """Updates client details."""
    name = client_data.get("name")
    if not name:
        return "Please specify client name to update."
        
    client = await resolve_client_fuzzy(db, user_id, name)
    if not client:
        return f"Client '{name}' not found."

    if client_data.get("email"):
        client.email = client_data["email"]
    if client_data.get("phone"):
        client.phone = client_data["phone"]
    if client_data.get("company"):
        client.company = client_data["company"]
    if client_data.get("notes"):
        client.notes = client_data["notes"]
    if client_data.get("priority_score") is not None:
        client.priority_score = client_data["priority_score"]

    await db.commit()
    await db.refresh(client)
    return f"Successfully updated client **{client.name}**."


async def delete_client(db: AsyncSession, user_id: UUID, name: str, confirmed: bool = False) -> dict:
    """Deletes a client with confirmation."""
    if not name:
        return {"needs_confirmation": False, "message": "Please specify client name to delete."}
    client = await resolve_client_fuzzy(db, user_id, name)
    if not client:
        return {"needs_confirmation": False, "message": f"Client '{name}' not found."}
        
    if not confirmed:
        return {
            "needs_confirmation": True,
            "message": f"⚠️ Are you sure you want to delete client '{client.name}'? Please choose Yes or No."
        }
        
    deleted_name = client.name
    await db.delete(client)
    await db.commit()
    return {"needs_confirmation": False, "message": f"Successfully deleted client **{deleted_name}**."}


async def resolve_client_fuzzy(db: AsyncSession, user_id: UUID, query_name: str) -> Optional[Client]:
    """Helper to resolve a client using fuzzy matching on name or company."""
    stmt = select(Client).filter(Client.user_id == user_id)
    clients = (await db.execute(stmt)).scalars().all()
    if not clients:
        return None

    best_match = None
    highest_score = 0.0

    for c in clients:
        score = max(
            fuzzy_score(query_name, c.name),
            fuzzy_score(query_name, c.company or "")
        )
        if score > highest_score:
            highest_score = score
            best_match = c

    if highest_score > 0.65:
        return best_match
    return None
