import math
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from backend.app.database import get_db
from backend.app.auth import require_role
from backend.app.models.incident import Incident
from backend.app.models.user import User
from backend.app.schemas.incident import (
    IncidentCreate, 
    IncidentUpdate, 
    IncidentResponse, 
    PaginatedIncidentResponse, 
    IncidentSummaryResponse
)

router = APIRouter()

VALID_INCIDENT_STATUS = ["Reported", "Under Investigation", "Resolved", "Closed"]

@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    incident: IncidentCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager"))
):
    """
    Create a new incident. Only HSE Managers can do this.
    """
    # Check for duplicate incident report (TC-09)
    duplicate_incident = db.query(Incident).filter(
        Incident.title == incident.title,
        Incident.location == incident.location,
        func.date(Incident.incident_date) == func.date(incident.incident_date)
    ).first()
    
    if duplicate_incident:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A potential duplicate incident report exists with the same title, location, and date."
        )

    db_incident = Incident(**incident.model_dump())
    db.add(db_incident)
    try:
        db.commit()
        db.refresh(db_incident)
        
        return db_incident
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Invalid reported_by user ID. The specified user does not exist."
        )

@router.get("/summary", response_model=IncidentSummaryResponse)
def get_incident_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager"))
):
    """
    Get the total count of incidents grouped by their status.
    """
    summary = db.query(
        Incident.status, 
        func.count(Incident.incident_id).label('count')
    ).group_by(Incident.status).all()
    
    status_counts = {item.status: item.count for item in summary}
    
    for s in VALID_INCIDENT_STATUS:
        if s not in status_counts:
            status_counts[s] = 0
            
    return IncidentSummaryResponse(status_counts=status_counts)

@router.get("/", response_model=PaginatedIncidentResponse)
def get_incidents(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager"))
):
    query = db.query(Incident)
    if status_filter:
        query = query.filter(Incident.status == status_filter)
        
    total_count = query.count()
    skip = (page - 1) * size
    incidents = query.offset(skip).limit(size).all()
    
    return PaginatedIncidentResponse(
        items=incidents,
        total_count=total_count,
        page=page,
        size=size
    )

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager"))
):
    db_incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return db_incident

@router.put("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: uuid.UUID, 
    incident_update: IncidentUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager"))
):
    db_incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    update_data = incident_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_incident, key, value)
        
    db.commit()
    db.refresh(db_incident)
    return db_incident

@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(
    incident_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager"))
):
    db_incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    try:
        db.delete(db_incident)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Cannot delete incident because it has associated tasks or trainings."
        )
    return None
