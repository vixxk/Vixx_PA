from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Client).filter(Client.user_id == current_user.id).order_by(Client.name.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check for duplicate
    dup_stmt = select(Client).filter(Client.user_id == current_user.id, Client.name.ilike(client_data.name))
    dup_res = await db.execute(dup_stmt)
    if dup_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Client '{client_data.name}' already exists."
        )

    client = Client(
        user_id=current_user.id,
        name=client_data.name,
        email=client_data.email,
        phone=client_data.phone,
        company=client_data.company,
        notes=client_data.notes,
        priority_score=client_data.priority_score or 70
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client

@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    client_data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Client).filter(Client.id == client_id, Client.user_id == current_user.id)
    result = await db.execute(stmt)
    client = result.scalars().first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
        
    update_dict = client_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(client, key, value)
        
    await db.commit()
    await db.refresh(client)
    return client

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Client).filter(Client.id == client_id, Client.user_id == current_user.id)
    result = await db.execute(stmt)
    client = result.scalars().first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
        
    await db.delete(client)
    await db.commit()
    return None
