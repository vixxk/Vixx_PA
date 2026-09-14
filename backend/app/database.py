from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import AsyncGenerator
import socket
from app.config import settings

# Prefer IPv4 address resolution for asyncpg to prevent IPv6 routing timeouts with Neon DB
_orig_getaddrinfo = socket.getaddrinfo
def _prefer_ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if family == socket.AF_UNSPEC or family == 0:
        family = socket.AF_INET
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _prefer_ipv4_getaddrinfo

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_recycle=1800
)

# Create sessionmaker for async sessions
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Declarative base class for models
Base = declarative_base()

# Dependency to get async database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
