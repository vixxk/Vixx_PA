from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class SessionState(Base):
    __tablename__ = "session_states"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    state = Column(JSON, nullable=False)
