from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.utils.auth_helper import get_current_user
from app.services import contact_service

router = APIRouter(prefix="/contacts", tags=["Contacts"])


class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=5)
    email: Optional[str] = None
    notes: Optional[str] = None


@router.get("/")
async def list_user_contacts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all contacts in the user's address book."""
    contacts = await contact_service.list_contacts(db, current_user.id)
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "phone": c.phone,
            "email": c.email,
            "notes": c.notes,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in contacts
    ]


@router.post("/")
async def create_or_update_contact(
    payload: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save or update a contact in the address book."""
    contact = await contact_service.save_contact(
        db=db,
        user_id=current_user.id,
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        notes=payload.notes
    )
    return {
        "id": str(contact.id),
        "name": contact.name,
        "phone": contact.phone,
        "email": contact.email,
        "notes": contact.notes
    }


@router.delete("/{name_or_id}")
async def remove_contact(
    name_or_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a contact by name or ID."""
    success = await contact_service.delete_contact(db, current_user.id, name_or_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact '{name_or_id}' not found.")
    return {"message": f"Contact '{name_or_id}' deleted successfully."}
