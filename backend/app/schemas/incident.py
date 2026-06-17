import uuid
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class IncidentBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    incident_type: str = Field(..., max_length=100)
    severity: Literal["Low", "Medium", "High", "Critical"]
    location: str
    proof_image_path: Optional[str] = None
    incident_date: datetime
    status: Literal["Reported", "Under Investigation", "Resolved", "Closed"] = "Reported"


class IncidentCreate(IncidentBase):
    reported_by: uuid.UUID


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    incident_type: Optional[str] = None
    severity: Optional[Literal["Low", "Medium", "High", "Critical"]] = None
    location: Optional[str] = None
    proof_image_path: Optional[str] = None
    incident_date: Optional[datetime] = None
    status: Optional[Literal["Reported", "Under Investigation", "Resolved", "Closed"]] = None


class IncidentResponse(IncidentBase):
    incident_id: uuid.UUID
    reported_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

from typing import List, Dict

class PaginatedIncidentResponse(BaseModel):
    items: List[IncidentResponse]
    total_count: int
    page: int
    size: int

class IncidentSummaryResponse(BaseModel):
    status_counts: Dict[str, int]