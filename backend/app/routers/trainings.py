from datetime import datetime, timedelta
from typing import List, Optional, Union
import uuid
from pydantic import BaseModel

from fastapi import Depends, APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import Base, SessionLocal, engine
from backend.app.models import Approval, Incident, Training, User
from backend.app.schemas import (
    TrainingCreate,
    TrainingResponse,
    TrainingUpdate,
    ApprovalCreate,
    ApprovalResponse,
)


# Local lightweight response model for employee training status
class EmployeeTrainingStatusResponse(BaseModel):
    training_id: uuid.UUID
    status: str
    start_date: datetime
    end_date: datetime
    incident_id: Optional[uuid.UUID] = None
    incident_title: Optional[str] = None

    class Config:
        from_attributes = True

router = APIRouter()

# ============================================================================
# Dependency to get database session
# ============================================================================

from backend.app.database import get_db

def _employee_training_status(training: Training):
    return {
        "training_id": training.training_id,
        "status": training.status,
        "start_date": training.start_date,
        "end_date": training.end_date,
        "incident_id": training.incident_id,
        "incident_title": training.incident.title if training.incident else None,
    }


@router.get("/", tags=["health"])
def read_root():
    return {"msg": "Trainings router active"}


# ============================================================================
# Training Endpoints
# ============================================================================

@router.get("/trainings", response_model=List[EmployeeTrainingStatusResponse])
def list_trainings(db: Session = Depends(get_db)):
    """Training list: returns training status, duration, and incident details."""
    trainings = db.query(Training).all()
    return [_employee_training_status(training) for training in trainings]


@router.get("/manager/trainings", response_model=List[TrainingResponse])
def manager_list_trainings(
    title: Optional[str] = Query(
        None,
        title="training title",
        description="Search trainings by title (used by managers)",
    ),
    db: Session = Depends(get_db),
):
    """Manager-only training list: search by title."""
    query = db.query(Training)

    if title:
        query = query.filter(Training.title.ilike(f"%{title}%"))

    return query.all()


@router.get("/trainings/{training_id}", response_model=Union[TrainingResponse, EmployeeTrainingStatusResponse])
def get_training(training_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific training by ID."""
    training = db.query(Training).filter(Training.training_id == training_id).first()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")
    return training


@router.post("/trainings", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
def create_training(training: TrainingCreate, db: Session = Depends(get_db)):
    """Create and assign a new training."""
    if training.incident_id:
        incident = db.query(Incident).filter(Incident.incident_id == training.incident_id).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with ID {training.incident_id} does not exist",
            )

    assigned_user = db.query(User).filter(User.user_id == training.assigned_to).first()
    if not assigned_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned user not found")

    new_training = Training(
        incident_id=training.incident_id,
        title=training.title,
        training_type=training.training_type,
        description=training.description,
        instructor=training.instructor,
        assigned_to=training.assigned_to,
        status=training.status,
        start_date=training.start_date,
        end_date=training.end_date,
        created_by=training.assigned_to,
    )
    db.add(new_training)
    db.commit()
    db.refresh(new_training)
    return new_training


@router.put("/trainings/{training_id}", response_model=TrainingResponse)
def update_training(
    training_id: uuid.UUID,
    training_update: TrainingUpdate,
    db: Session = Depends(get_db),
):
    """Update a training status."""
    training = db.query(Training).filter(Training.training_id == training_id).first()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")

    update_data = training_update.dict(exclude_unset=True)
    if "assigned_to" in update_data:
        assigned_user = db.query(User).filter(User.user_id == update_data["assigned_to"]).first()
        if not assigned_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned user not found")

    for field, value in update_data.items():
        setattr(training, field, value)

    db.commit()
    db.refresh(training)
    return training


@router.post("/trainings/{training_id}/approvals", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
def request_training_approval(training_id: uuid.UUID, approval: ApprovalCreate, db: Session = Depends(get_db)):
    """Create a manager approval request for a completed training."""
    training = db.query(Training).filter(Training.training_id == training_id).first()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")
    if training.status != "Completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approval can only be requested after training has been completed",
        )
    if approval.module_type != "TRAINING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="module_type must be TRAINING for training approvals",
        )
    if approval.reference_id != training_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reference_id must match the training_id in the URL",
        )

    requested_by = db.query(User).filter(User.user_id == approval.requested_by).first()
    if not requested_by:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested user not found")

    if approval.approved_by is not None:
        approved_by = db.query(User).filter(User.user_id == approval.approved_by).first()
        if not approved_by:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approver user not found")

    new_approval = Approval(
        module_type=approval.module_type,
        reference_id=approval.reference_id,
        requested_by=approval.requested_by,
        approved_by=approval.approved_by,
        status=approval.status,
        comments=approval.comments,
    )
    db.add(new_approval)
    db.commit()
    db.refresh(new_approval)
    return new_approval



@router.get("/approvals/{approval_id}", response_model=ApprovalResponse)
def get_approval(approval_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific approval request."""
    approval = db.query(Approval).filter(Approval.approval_id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    return approval


@router.delete("/trainings/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_training(training_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a training."""
    training = db.query(Training).filter(Training.training_id == training_id).first()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")

    db.delete(training)
    db.commit()
    return None

