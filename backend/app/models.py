import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Date, Text, func, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, foreign
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String(20), nullable=True)
    role = Column(String(20), nullable=False, default="Employee")  # 'Admin', 'HSE Manager', 'Employee'
    status = Column(String(20), nullable=False, default="Active")   # 'Active', 'Inactive'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    incidents_reported = relationship("Incident", back_populates="reporter", foreign_keys="[Incident.reported_by]")
    incidents_assigned = relationship("Incident", back_populates="assignee", foreign_keys="[Incident.assigned_to]")
    tasks_assigned = relationship("Task", back_populates="assignee", foreign_keys="[Task.assigned_to]")
    tasks_created = relationship("Task", back_populates="creator", foreign_keys="[Task.created_by]")
    tasks_reviewed = relationship("Task", back_populates="reviewer", foreign_keys="[Task.reviewed_by]")
    approvals_requested = relationship("Approval", back_populates="requester", foreign_keys="[Approval.requested_by]")
    approvals_actioned = relationship("Approval", back_populates="approver", foreign_keys="[Approval.approved_by]")
    trainings_assigned = relationship("Training", back_populates="assignee", foreign_keys="[Training.assigned_to]")
    trainings_created = relationship("Training", back_populates="creator", foreign_keys="[Training.created_by]")


class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    incident_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # 'Low', 'Medium', 'High', 'Critical'
    location = Column(String(255), nullable=False)
    proof_image_path = Column(String(500), nullable=True)
    incident_date = Column(Date, nullable=False)  # Actual date the incident occurred
    status = Column(String(50), nullable=False, default="Reported")  # 'Reported', 'Under Investigation', 'Resolved', 'Closed'
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    reporter = relationship("User", back_populates="incidents_reported", foreign_keys=[reported_by])
    assignee = relationship("User", back_populates="incidents_assigned", foreign_keys=[assigned_to])
    tasks = relationship("Task", back_populates="incident")
    trainings = relationship("Training", back_populates="incident")


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="Medium")  # 'Low', 'Medium', 'High', 'Urgent'
    status = Column(String(20), nullable=False, default="To Do")  # 'To Do', 'In Progress', 'Review', 'Done'
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.incident_id", ondelete="SET NULL"), nullable=True)
    due_date = Column(Date, nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)

    # Relationships
    assignee = relationship("User", back_populates="tasks_assigned", foreign_keys=[assigned_to])
    creator = relationship("User", back_populates="tasks_created", foreign_keys=[created_by])
    reviewer = relationship("User", back_populates="tasks_reviewed", foreign_keys=[reviewed_by])
    incident = relationship("Incident", back_populates="tasks")


class Approval(Base):
    __tablename__ = "approvals"

    approval_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_type = Column(String(20), nullable=False)  # 'TASK', 'TRAINING'
    reference_id = Column(UUID(as_uuid=True), nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), nullable=False, default="Pending")  # 'Pending', 'Approved', 'Rejected'
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    requester = relationship("User", back_populates="approvals_requested", foreign_keys=[requested_by])
    approver = relationship("User", back_populates="approvals_actioned", foreign_keys=[approved_by])
    
    # Polymorphic relationships based on module_type
    task = relationship(
        "Task",
        primaryjoin=lambda: and_(
            Approval.module_type == "TASK",
            foreign(Approval.reference_id) == Task.task_id
        ),
        viewonly=True,
        uselist=False
    )
    training = relationship(
        "Training",
        primaryjoin=lambda: and_(
            Approval.module_type == "TRAINING",
            foreign(Approval.reference_id) == Training.training_id
        ),
        viewonly=True,
        uselist=False
    )


class Training(Base):
    __tablename__ = "trainings"

    training_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.incident_id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    training_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    instructor = Column(String(255), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(20), nullable=False, default="Assigned")  # 'Assigned', 'In Progress', 'Completed'
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    incident = relationship("Incident", back_populates="trainings")
    assignee = relationship("User", back_populates="trainings_assigned", foreign_keys=[assigned_to])
    creator = relationship("User", back_populates="trainings_created", foreign_keys=[created_by])

