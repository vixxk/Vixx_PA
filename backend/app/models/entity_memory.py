"""
Entity Memory model — stores learned facts about entities across conversations.
"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class EntityMemory(Base):
    __tablename__ = "entity_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # 'project', 'client', 'payment', 'task'
    entity_id = Column(UUID(as_uuid=True), nullable=True)  # FK to the actual entity (optional)
    entity_name = Column(String(255), nullable=True)
    fact = Column(Text, nullable=False)  # "Client prefers weekly updates", "Payment always in USD"
    source_session_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at = Column(DateTime(timezone=True), server_default=func.now())
