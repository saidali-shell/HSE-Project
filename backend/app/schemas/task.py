import uuid
from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    priority: Literal["Low", "Medium", "High", "Urgent"] = "Medium"
    status: Literal["To Do", "In Progress", "Review", "Done"] = "To Do"
    due_date: date
    is_deleted: bool = False


class TaskCreate(TaskBase):
    assigned_to: uuid.UUID
    incident_id: uuid.UUID


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    priority: Optional[Literal["Low", "Medium", "High", "Urgent"]] = None
    status: Optional[Literal["To Do", "In Progress", "Review", "Done"]] = None
    assigned_to: Optional[uuid.UUID] = None
    incident_id: Optional[uuid.UUID] = None
    due_date: Optional[date] = None
    is_deleted: Optional[bool] = None


class StatusUpdate(BaseModel):
    status: Literal["To Do", "In Progress", "Review", "Done"]


class TaskResponse(TaskBase):
    task_id: uuid.UUID
    assigned_to: uuid.UUID
    created_by: uuid.UUID
    incident_id: uuid.UUID
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True