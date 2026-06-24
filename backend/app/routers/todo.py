from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.models.todo import Todo
from app.models.project import Project
from app.models.user import User
from app.schemas.todo import TodoCreate, TodoUpdate, TodoResponse
from app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/todos", tags=["Todos"])

@router.get("/", response_model=List[TodoResponse])
async def list_todos(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Retrieve todos. Must make sure project belongs to the user.
    query = select(Todo).join(Project).filter(Project.user_id == current_user.id)
    if project_id:
        query = query.filter(Todo.project_id == project_id)

    result = await db.execute(query.order_by(Todo.created_at.desc()))
    return result.scalars().all()

@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo_data: TodoCreate,
    x_google_token: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify project belongs to current user
    project_result = await db.execute(
        select(Project).filter(Project.id == todo_data.project_id, Project.user_id == current_user.id)
    )
    project = project_result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    todo = Todo(
        project_id=todo_data.project_id,
        milestone_id=todo_data.milestone_id,
        title=todo_data.title,
        description=todo_data.description,
        priority=todo_data.priority,
        status=todo_data.status,
        due_date=todo_data.due_date,
        estimated_hours=todo_data.estimated_hours,
        actual_hours=todo_data.actual_hours
    )
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    
    return todo

@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Todo).join(Project).filter(Todo.id == todo_id, Project.user_id == current_user.id)
    )
    todo = result.scalars().first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    return todo

@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: UUID,
    todo_data: TodoUpdate,
    x_google_token: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Todo).join(Project).filter(Todo.id == todo_id, Project.user_id == current_user.id)
    )
    todo = result.scalars().first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )

    update_dict = todo_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(todo, key, value)

    await db.commit()
    await db.refresh(todo)
    
    return todo

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: UUID,
    x_google_token: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Todo).join(Project).filter(Todo.id == todo_id, Project.user_id == current_user.id)
    )
    todo = result.scalars().first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )

    await db.delete(todo)
    await db.commit()
    
    return None
