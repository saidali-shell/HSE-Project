import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Date, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Training(Base):
    __tablename__ = "trainings"

    training_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.incident_id", ondelete="RESTRICT"), nullable=False)
    title = Column(String(255), nullable=False)
    training_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    instructor = Column(String(255), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(20), nullable=False, default="Incomplete")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    incident = relationship("Incident", back_populates="trainings")
    assignee = relationship("User", back_populates="trainings_assigned", foreign_keys=[assigned_to])
    creator = relationship("User", back_populates="trainings_created", foreign_keys=[created_by])