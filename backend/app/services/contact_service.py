"""
Contact Service — Manages address book / contact name resolution for WhatsApp and communications.
"""

import re
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.models.contact import Contact
from app.utils.green_api_helper import format_whatsapp_chat_id


def is_phone_number(text: str) -> bool:
    """Checks if a string is primarily a numeric phone number."""
    cleaned = text.strip()
    digits = re.sub(r"\D", "", cleaned)
    # If 10 or more digits, or starts with '+' and has at least 8 digits
    if len(digits) >= 10 or (cleaned.startswith("+") and len(digits) >= 7):
        return True
    return False


def is_email_address(text: str) -> bool:
    """Checks if a string is a valid email address."""
    cleaned = text.strip()
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, cleaned))


async def resolve_contact_email(
    db: AsyncSession,
    user_id: UUID,
    name_or_email: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolves an input into (contact_name, email_address).
    If input is already an email address, returns (None, email).
    Otherwise, queries user contacts by name.
    """
    if not name_or_email:
        return None, None

    cleaned = name_or_email.strip()

    if is_email_address(cleaned):
        return None, cleaned

    name_query = cleaned.lower()
    stmt = select(Contact).filter(
        Contact.user_id == user_id,
        Contact.name.ilike(f"%{name_query}%")
    ).order_by(desc(Contact.created_at))

    result = await db.execute(stmt)
    contacts = result.scalars().all()

    for c in contacts:
        if c.name.strip().lower() == name_query:
            return c.name, c.email

    if contacts:
        return contacts[0].name, contacts[0].email

    return cleaned, None


async def resolve_contact(
    db: AsyncSession,
    user_id: UUID,
    name_or_phone: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolves an input into (contact_name, phone_number).
    If input is already a phone number, returns (None, phone_number).
    Otherwise, queries the user's contacts by name.
    """
    if not name_or_phone:
        return None, None

    cleaned = name_or_phone.strip()

    # Direct phone number
    if is_phone_number(cleaned):
        return None, cleaned

    # Search in database by name
    name_query = cleaned.lower()
    stmt = select(Contact).filter(
        Contact.user_id == user_id,
        Contact.name.ilike(f"%{name_query}%")
    ).order_by(desc(Contact.created_at))

    result = await db.execute(stmt)
    contacts = result.scalars().all()

    # Exact match preferred
    for c in contacts:
        if c.name.strip().lower() == name_query:
            return c.name, c.phone

    # Fuzzy/prefix match
    if contacts:
        return contacts[0].name, contacts[0].phone

    return cleaned, None


async def save_contact(
    db: AsyncSession,
    user_id: UUID,
    name: str,
    phone: str,
    email: Optional[str] = None,
    notes: Optional[str] = None
) -> Contact:
    """Saves or updates a contact in the user's address book."""
    cleaned_name = name.strip()
    cleaned_phone = phone.strip()

    # Check if contact with same name already exists
    stmt = select(Contact).filter(
        Contact.user_id == user_id,
        Contact.name.ilike(cleaned_name)
    )
    res = await db.execute(stmt)
    existing = res.scalars().first()

    if existing:
        existing.phone = cleaned_phone
        if email:
            existing.email = email.strip()
        if notes:
            existing.notes = notes.strip()
        await db.commit()
        await db.refresh(existing)
        return existing

    new_contact = Contact(
        user_id=user_id,
        name=cleaned_name,
        phone=cleaned_phone,
        email=email.strip() if email else None,
        notes=notes.strip() if notes else None
    )
    db.add(new_contact)
    await db.commit()
    await db.refresh(new_contact)
    return new_contact


async def list_contacts(db: AsyncSession, user_id: UUID) -> List[Contact]:
    """Retrieves all contacts saved by the user."""
    stmt = select(Contact).filter(Contact.user_id == user_id).order_by(Contact.name.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def delete_contact(db: AsyncSession, user_id: UUID, name_or_id: str) -> bool:
    """Deletes a contact by name or UUID."""
    cleaned = name_or_id.strip()
    stmt = select(Contact).filter(Contact.user_id == user_id)

    matched = None
    try:
        val_uuid = UUID(cleaned)
        stmt_uuid = stmt.filter(Contact.id == val_uuid)
        res = await db.execute(stmt_uuid)
        matched = res.scalars().first()
    except ValueError:
        pass

    if not matched:
        stmt_name = stmt.filter(Contact.name.ilike(cleaned))
        res = await db.execute(stmt_name)
        matched = res.scalars().first()

    if matched:
        await db.delete(matched)
        await db.commit()
        return True
    return False
