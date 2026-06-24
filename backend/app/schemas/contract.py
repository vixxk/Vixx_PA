from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class ContractBase(BaseModel):
    project_id: UUID
    client_name: str
    received_date: Optional[datetime] = None
    signed_date: Optional[datetime] = None
    contract_url: Optional[str] = None
    notes: Optional[str] = None

class ContractCreate(ContractBase):
    pass

class ContractUpdate(BaseModel):
    client_name: Optional[str] = None
    received_date: Optional[datetime] = None
    signed_date: Optional[datetime] = None
    contract_url: Optional[str] = None
    notes: Optional[str] = None

class ContractResponse(ContractBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
