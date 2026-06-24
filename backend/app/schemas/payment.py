from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal

class PaymentBase(BaseModel):
    project_id: UUID
    amount: Decimal
    currency: Optional[str] = "INR"
    payment_type: str # Advance, Partial, Final
    received_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = "pending" # pending, received, overdue
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    payment_type: Optional[str] = None
    received_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class PaymentResponse(PaymentBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
