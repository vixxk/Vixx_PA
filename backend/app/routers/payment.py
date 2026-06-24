from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.payment import Payment
from app.models.project import Project
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse
from app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.get("/", response_model=List[PaymentResponse])
async def list_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch projects of current user first
    proj_stmt = select(Project.id).filter(Project.user_id == current_user.id)
    proj_result = await db.execute(proj_stmt)
    proj_ids = proj_result.scalars().all()
    
    if not proj_ids:
        return []
        
    result = await db.execute(
        select(Payment).filter(Payment.project_id.in_(proj_ids)).order_by(Payment.created_at.desc())
    )
    return result.scalars().all()

@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate project belongs to user
    proj_stmt = select(Project).filter(Project.id == payment_data.project_id, Project.user_id == current_user.id)
    proj_result = await db.execute(proj_stmt)
    project = proj_result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
        
    payment = Payment(
        project_id=payment_data.project_id,
        amount=payment_data.amount,
        currency=payment_data.currency,
        payment_type=payment_data.payment_type,
        received_date=payment_data.received_date,
        due_date=payment_data.due_date,
        status=payment_data.status,
        notes=payment_data.notes
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    
    return payment

@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: UUID,
    payment_data: PaymentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Payment).join(Project).filter(Payment.id == payment_id, Project.user_id == current_user.id)
    result = await db.execute(stmt)
    payment = result.scalars().first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
        
    update_dict = payment_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(payment, key, value)
        
    await db.commit()
    await db.refresh(payment)
    
    return payment

@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Payment).join(Project).filter(Payment.id == payment_id, Project.user_id == current_user.id)
    result = await db.execute(stmt)
    payment = result.scalars().first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
        
    await db.delete(payment)
    await db.commit()
    
    return None

