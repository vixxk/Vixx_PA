import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="planning") # planning, developing, finished
    priority = Column(String(50), nullable=True, default=None) # low, medium, high, critical
    deadline = Column(DateTime(timezone=True), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=True, default=0.0)
    summary = Column(Text, nullable=True)
    notepad = Column(Text, nullable=True)
    risks = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    todos = relationship("Todo", back_populates="project", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="project", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="project", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="project", cascade="all, delete-orphan")
    pending_things = relationship("PendingThing", back_populates="project", cascade="all, delete-orphan")

