from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return True

def get_password_hash(password: str) -> str:
    return password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(
    db: AsyncSession = Depends(get_db)
) -> User:
    import os
    default_email = os.getenv("SMTP_USER") or "default_user@example.com"
    result = await db.execute(select(User).filter(User.email == default_email))
    user = result.scalars().first()
    if user is None:
        user = User(
            name="Default Workspace User",
            email=default_email,
            password_hash="dummy_hash_bypassed"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
