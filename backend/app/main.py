from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import auth, project, todo, timeline, ai, sync, payment, contract, pending_thing, reminder, whatsapp, contact, email
from fastapi.staticfiles import StaticFiles
import os


# Initialize FastAPI App (Reloader touched)
app = FastAPI(
    title="Personal Assistant API",
    description="Backend API for Personal Assistant incorporating LangGraph agentic workflows and PostgreSQL CRUD.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
async def on_startup():
    from sqlalchemy import text
    # Automatically create tables in database if they do not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text('ALTER TABLE scheduled_messages ADD COLUMN IF NOT EXISTS subject VARCHAR(255);'))
        await conn.execute(text('ALTER TABLE contacts ADD COLUMN IF NOT EXISTS email VARCHAR(255);'))
        
    import asyncio
    from app.utils.reminder_daemon import start_reminder_daemon
    asyncio.create_task(start_reminder_daemon())

# Setup CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under api/v1 prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(project.router, prefix="/api/v1")
app.include_router(todo.router, prefix="/api/v1")
app.include_router(timeline.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
app.include_router(payment.router, prefix="/api/v1")
app.include_router(contract.router, prefix="/api/v1")
app.include_router(pending_thing.router, prefix="/api/v1")
app.include_router(reminder.router, prefix="/api/v1")
app.include_router(whatsapp.router, prefix="/api/v1")
app.include_router(contact.router, prefix="/api/v1")
app.include_router(email.router, prefix="/api/v1")

# Mount static uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "message": "Backend service is up and running"
    }


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "healthy",
        "message": "Welcome to the Personal Assistant API",
        "debug_mode": settings.DEBUG
    }

