import uuid
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class ApprovalBase(BaseModel):
    module_type: Literal["TASK", "TRAINING"]
    reference_id: uuid.UUID
    status: Literal["Pending", "Approved", "Rejected"] = "Pending"
    comments: Optional[str] = None


class ApprovalCreate(ApprovalBase):
    requested_by: uuid.UUID
    approved_by: Optional[uuid.UUID] = None


class ApprovalUpdate(BaseModel):
    status: Optional[Literal["Pending", "Approved", "Rejected"]] = None
    comments: Optional[str] = None
    approved_by: Optional[uuid.UUID] = None


class ApprovalResponse(ApprovalBase):
    approval_id: uuid.UUID
    requested_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True