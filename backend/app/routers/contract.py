from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID, uuid4
import os
import shutil

from app.database import get_db
from app.models.contract import Contract
from app.models.project import Project
from app.models.user import User
from app.schemas.contract import ContractResponse, ContractUpdate
from app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/contracts", tags=["Contracts"])

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[ContractResponse])
async def list_contracts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    proj_stmt = select(Project.id).filter(Project.user_id == current_user.id)
    proj_result = await db.execute(proj_stmt)
    proj_ids = proj_result.scalars().all()
    
    if not proj_ids:
        return []
        
    result = await db.execute(
        select(Contract).filter(Contract.project_id.in_(proj_ids)).order_by(Contract.created_at.desc())
    )
    return result.scalars().all()

@router.post("/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    project_id: UUID = Form(...),
    client_name: str = Form(...),
    notes: Optional[str] = Form(None),
    received_date: Optional[str] = Form(None),
    signed_date: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate project
    proj_stmt = select(Project).filter(Project.id == project_id, Project.user_id == current_user.id)
    proj_result = await db.execute(proj_stmt)
    project = proj_result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
        
    contract_url = None
    if file:
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # URL path to access static file
        contract_url = f"/uploads/{unique_filename}"
        
    import dateutil.parser
    rec_dt = None
    sig_dt = None
    if received_date:
        try: rec_dt = dateutil.parser.parse(received_date)
        except: pass
    if signed_date:
        try: sig_dt = dateutil.parser.parse(signed_date)
        except: pass

    contract = Contract(
        project_id=project_id,
        client_name=client_name,
        received_date=rec_dt,
        signed_date=sig_dt,
        contract_url=contract_url,
        notes=notes
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    return contract

@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: UUID,
    contract_data: ContractUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Contract).join(Project).filter(Contract.id == contract_id, Project.user_id == current_user.id)
    result = await db.execute(stmt)
    contract = result.scalars().first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
        
    update_dict = contract_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(contract, key, value)
        
    await db.commit()
    await db.refresh(contract)
    return contract

@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Contract).join(Project).filter(Contract.id == contract_id, Project.user_id == current_user.id)
    result = await db.execute(stmt)
    contract = result.scalars().first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
        
    # Delete local file if exists
    if contract.contract_url and contract.contract_url.startswith("/uploads/"):
        filename = contract.contract_url.replace("/uploads/", "")
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
            
    await db.delete(contract)
    await db.commit()
    return None
