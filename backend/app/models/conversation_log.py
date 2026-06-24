"""
Conversation Log model — stores all messages for persistent memory.
"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base


class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    intent = Column(String(100), nullable=True)  # classified intent for this turn
    entities = Column(JSONB, nullable=True)  # extracted entities: {project: "Alpha", client: "Acme"}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
