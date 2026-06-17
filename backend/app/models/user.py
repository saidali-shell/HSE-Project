import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String(20), nullable=True)
    role = Column(String(20), nullable=False, default="Employee")
    status = Column(String(20), nullable=False, default="Active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    incidents_reported = relationship("Incident", back_populates="reporter", foreign_keys="[Incident.reported_by]")
    tasks_assigned = relationship("Task", back_populates="assignee", foreign_keys="[Task.assigned_to]")
    tasks_created = relationship("Task", back_populates="creator", foreign_keys="[Task.created_by]")
    tasks_reviewed = relationship("Task", back_populates="reviewer", foreign_keys="[Task.reviewed_by]")
    approvals_requested = relationship("Approval", back_populates="requester", foreign_keys="[Approval.requested_by]")
    approvals_actioned = relationship("Approval", back_populates="approver", foreign_keys="[Approval.approved_by]")
    trainings_assigned = relationship("Training", back_populates="assignee", foreign_keys="[Training.assigned_to]")
    trainings_created = relationship("Training", back_populates="creator", foreign_keys="[Training.created_by]")