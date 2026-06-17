import uuid
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class TrainingBase(BaseModel):
    incident_id: uuid.UUID
    title: str = Field(..., max_length=255)
    training_type: str = Field(..., max_length=100)
    description: str
    instructor: str = Field(..., max_length=255)
    assigned_to: uuid.UUID
    status: Literal["Completed", "Incomplete"] = "Incomplete"
    start_date: datetime
    end_date: datetime


class TrainingCreate(TrainingBase):
    pass


class TrainingUpdate(BaseModel):
    title: Optional[str] = None
    training_type: Optional[str] = None
    description: Optional[str] = None
    instructor: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    incident_id: Optional[uuid.UUID] = None
    status: Optional[Literal["Completed", "Incomplete"]] = None


class TrainingResponse(TrainingBase):
    training_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True