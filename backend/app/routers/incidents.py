import math
import uuid
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from backend.app.database import get_db
from backend.app.auth import require_role
from backend.app.models.incident import Incident
from backend.app.models.user import User
from backend.app.models.task import Task
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
    current_user: User = Depends(require_role("HSE Manager", "Admin"))
):
    """
    Create a new incident. Only HSE Managers or Admins can do this.
    """
    db_incident = Incident(**incident.model_dump())
    db.add(db_incident)
    try:
        db.flush() # Flush to get the generated incident_id
        
        # Auto-create an investigation task
        investigation_task = Task(
            title=f"Investigation: {db_incident.title}",
            description=f"Automatically generated investigation task for Incident: {db_incident.title}",
            priority=db_incident.severity,
            status="To Do",
            assigned_to=db_incident.reported_by,
            created_by=db_incident.reported_by,
            incident_id=db_incident.incident_id,
            due_date=date.today() + timedelta(days=7)
        )
        db.add(investigation_task)
        
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
def get_incident_summary(db: Session = Depends(get_db)):
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
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    query = db.query(Incident)
    if status_filter:
        query = query.filter(Incident.status == status_filter)
        
    total_count = query.count()
    incidents = query.offset(skip).limit(limit).all()
    
    return PaginatedIncidentResponse(
        items=incidents,
        total_count=total_count,
        page=(skip // limit) + 1,
        size=limit
    )

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    db_incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return db_incident

@router.put("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: uuid.UUID, 
    incident_update: IncidentUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager", "Admin"))
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
    current_user: User = Depends(require_role("Admin"))
):
    db_incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    db.delete(db_incident)
    db.commit()
    return None
