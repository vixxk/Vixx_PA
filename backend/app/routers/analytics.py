from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from app.database import get_db
from app.models.user import User
from app.services import analytics_service
from app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/")
async def get_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    return await analytics_service.get_dashboard_analytics(db, current_user.id)
