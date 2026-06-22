import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, foreign

from backend.app.database import Base
from backend.app.models.task import Task
from backend.app.models.training import Training


class Approval(Base):
    __tablename__ = "approvals"

    approval_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_type = Column(String(20), nullable=False)
    reference_id = Column(UUID(as_uuid=True), nullable=False)
    requested_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False
    )
    approved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )
    status = Column(String(20), nullable=False, default="Pending")
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    requester = relationship(
        "User",
        back_populates="approvals_requested",
        foreign_keys=[requested_by]
    )

    approver = relationship(
        "User",
        back_populates="approvals_actioned",
        foreign_keys=[approved_by]
    )

    # TASK approval
    task = relationship(
        "Task",
        primaryjoin=lambda: and_(
            Approval.module_type == "TASK",
            foreign(Approval.reference_id) == Task.task_id
        ),
        viewonly=True,
        uselist=False
    )

    # TRAINING approval
    training = relationship(
        "Training",
        primaryjoin=lambda: and_(
            Approval.module_type == "TRAINING",
            foreign(Approval.reference_id) == Training.training_id
        ),
        viewonly=True,
        uselist=False
    )