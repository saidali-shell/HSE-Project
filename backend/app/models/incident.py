import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Date, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    incident_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    location = Column(String(255), nullable=False)
    proof_image_path = Column(String(500), nullable=True)
    incident_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default="Reported")
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


    # Relationships
    reporter = relationship("User", back_populates="incidents_reported", foreign_keys=[reported_by])

    tasks = relationship("Task", back_populates="incident")
    trainings = relationship("Training", back_populates="incident")
    history = relationship("IncidentHistory", back_populates="incident", cascade="all, delete-orphan")

class IncidentHistory(Base):
    __tablename__ = "incident_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    action = Column(String(50), nullable=False) # e.g. "Status Changed", "Incident Created", "Edited"
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    incident = relationship("Incident", back_populates="history")
    user = relationship("User")