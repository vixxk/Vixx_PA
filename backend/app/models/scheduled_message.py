import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient = Column(String(100), nullable=False)
    recipient_name = Column(String(100), nullable=True)
    subject = Column(String(255), nullable=True)  # For emails
    message = Column(Text, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    channel = Column(String(50), nullable=False, default="whatsapp")  # 'whatsapp', 'email', 'sms'
    status = Column(String(50), nullable=False, default="pending")    # 'pending', 'sent', 'failed', 'cancelled'
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="scheduled_messages")
