from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional
import httpx
from uuid import UUID

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.project import Project
from app.models.milestone import Milestone
from app.models.todo import Todo
from app.utils.auth_helper import get_current_user
from app.tools.calendar_tool import sync_milestones_to_calendar
from app.tools.github_tool import sync_todos_to_github

router = APIRouter(prefix="/sync", tags=["Integrations Sync"])

class SheetsSyncRequest(BaseModel):
    access_token: str
    project_id: UUID

class CalendarSyncRequest(BaseModel):
    access_token: str
    project_id: UUID

class GitHubSyncRequest(BaseModel):
    token: str
    repo: str # "owner/repo"
    project_id: UUID

@router.get("/google/auth")
async def google_auth():
    """
    Returns the Google OAuth login url.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=400, detail="Google OAuth client keys are not configured.")
        
    scopes = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/calendar"
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={scopes}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return {"url": auth_url}

@router.get("/google/callback")
async def google_callback(code: str = Query(...)):
    """
    Callback URI to exchange authorization code for Google Access/Refresh tokens.
    """
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        res = await client.post(token_url, data=data)
        if res.status_code != 200:
            return RedirectResponse(url=f"http://localhost:5173/?error=oauth_exchange_failed")
            
        token_data = res.json()
        access_token = token_data.get("access_token")
        
        # Redirect back to frontend with access token parameter
        return RedirectResponse(url=f"http://localhost:5173/?google_token={access_token}")

@router.post("/sheets")
async def sync_sheets():
    raise HTTPException(status_code=400, detail="Google Sheets integration has been disabled. All logic is now stored in PostgreSQL.")

@router.post("/calendar")
async def sync_calendar(req: CalendarSyncRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Fetch milestones
    milestones_res = await db.execute(
        select(Milestone).filter(Milestone.project_id == req.project_id)
    )
    milestones = milestones_res.scalars().all()
    milestone_dicts = [
        {
            "title": m.title,
            "description": m.description,
            "start_date": m.start_date.strftime("%Y-%m-%d") if m.start_date else None,
            "end_date": m.end_date.strftime("%Y-%m-%d") if m.end_date else None,
        }
        for m in milestones
    ]
    
    results = await sync_milestones_to_calendar(
        access_token=req.access_token,
        milestones=milestone_dicts
    )
    return {"success": True, "sync_results": results}

@router.post("/github")
async def sync_github(req: GitHubSyncRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Fetch todos
    todos_res = await db.execute(
        select(Todo).filter(Todo.project_id == req.project_id)
    )
    todos = todos_res.scalars().all()
    todo_dicts = [
        {
            "title": t.title,
            "description": t.description,
            "priority": t.priority,
            "estimated_hours": float(t.estimated_hours) if t.estimated_hours else None,
        }
        for t in todos
    ]
    
    results = await sync_todos_to_github(
        token=req.token,
        repo=req.repo,
        todos=todo_dicts
    )
    return {"success": True, "sync_results": results}

@router.get("/sheets/links")
async def get_sheets_links(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return {
        "payments_url": None
    }
