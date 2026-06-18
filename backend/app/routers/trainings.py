from datetime import datetime, timedelta, date
from typing import List, Optional, Union
import uuid
from pydantic import BaseModel

from fastapi import Depends, APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import Base, SessionLocal, engine
from backend.app.models import Incident, Training, User, Approval
from backend.app.schemas import (
    TrainingCreate,
    TrainingResponse,
    TrainingUpdate,
    ApprovalResponse,
)
from backend.app.auth import require_role, get_current_user


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
def list_trainings(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager", "Admin")),
):
    offset = (page - 1) * size

    trainings = (
        db.query(Training)
        .offset(offset)
        .limit(size)
        .all()
    )

    return [_employee_training_status(training) for training in trainings]
@router.get("/manager/trainings", response_model=Union[List[TrainingResponse], dict])
def manager_list_trainings(
    title: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager", "Admin")),
):
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="To Date cannot be earlier than From Date",
        )

    query = db.query(Training)

    if title:
        query = query.filter(
            Training.title.ilike(f"%{title}%")
        )

    if start_date:
        query = query.filter(Training.start_date >= start_date)
    if end_date:
        query = query.filter(Training.end_date <= end_date)

    offset = (page - 1) * size

    trainings = (
        query
        .offset(offset)
        .limit(size)
        .all()
    )

    if (start_date or end_date) and not trainings:
        return {"message": "No training records exist within the selected date range."}

    return trainings



@router.get("/trainings/{training_id}", response_model=Union[TrainingResponse, EmployeeTrainingStatusResponse])
def get_training(training_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_role("HSE Manager", "Admin"))):
    """Get a specific training by ID."""
    training = db.query(Training).filter(Training.training_id == training_id).first()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")
    return training


@router.post("/trainings", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
def create_training(
    training: TrainingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager")),
):
    """Create and assign a new training.

    Only HSE Manager users can create trainings and assign them to employees.
    """
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
    if assigned_user.role != "Employee":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Training can only be assigned to an Employee")

    duplicate_training = db.query(Training).filter(
        Training.title == training.title,
        Training.assigned_to == training.assigned_to,
    ).first()
    if duplicate_training:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee is already enrolled in this training program",
        )

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
        created_by=current_user.user_id,
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
    current_user: User = Depends(require_role("HSE Manager", "Admin")),
):
    """Update a training status."""
    training = db.query(Training).filter(Training.training_id == training_id).first()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")

    update_data = training_update.dict(exclude_unset=True)
    if "assigned_to" in update_data:
        assigned_user = db.query(User).filter(User.user_id == update_data["assigned_to"]).first()
        if not assigned_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assigned user with ID {update_data['assigned_to']} not found")
        if assigned_user.role != "Employee":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Training can only be assigned to a user with role Employee")

    # remember old status to detect manager action on a review
    old_status = training.status

    for field, value in update_data.items():
        setattr(training, field, value)

    db.commit()
    db.refresh(training)

    # If the training was in 'Review' and manager changed it to Completed/Incomplete,
    # reflect that decision on any pending Approval records for this training so the audit trail matches.
    if "status" in update_data and old_status == "Review":
        pending_approvals = db.query(Approval).filter(
            Approval.module_type == "TRAINING",
            Approval.reference_id == training_id,
            Approval.status == "Pending",
        ).all()

        for pa in pending_approvals:
            if training.status == "Completed":
                pa.status = "Approved"
            else:
                pa.status = "Rejected"

        if pending_approvals:
            db.commit()

    return training


@router.delete("/trainings/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_training(training_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_role("HSE Manager", "Admin"))):
    """Delete a training."""
    training = db.query(Training).filter(Training.training_id == training_id).first()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")

    db.delete(training)
    db.commit()
    return None


@router.get("/trainings/user/{user_id}", response_model=Union[List[TrainingResponse], dict])
def get_trainings_by_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allow an employee to view trainings assigned to a specific user ID."""
    if current_user.role == "Employee" and current_user.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to view this user's trainings")

    if not db.query(User).filter(User.user_id == user_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No user found with ID {user_id}")

    trainings = db.query(Training).filter(Training.assigned_to == user_id).all()
    if current_user.role == "Employee" and not trainings:
        return {"message": "No Training Assigned"}
    return trainings


@router.patch("/trainings/{training_id}/request-review", response_model=ApprovalResponse)
def request_training_review(
    training_id: uuid.UUID,
    training_update: TrainingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employee or manager requests a review/approval for a training.

    If an Employee calls this, they may only request review for their own training.
    Managers may request review for any training.
    """
    training = db.query(Training).filter(Training.training_id == training_id).first()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")

    if current_user.role == "Employee" and current_user.user_id != training.assigned_to:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to request review for this training")

    update_data = training_update.dict(exclude_unset=True)

    training.status = "Review"

    new_approval = Approval(
        module_type="TRAINING",
        reference_id=training_id,
        requested_by=current_user.user_id,
        comments=update_data.get("comments", None),
        status="Pending",
    )

    db.add(new_approval)
    db.commit()
    db.refresh(new_approval)
    db.refresh(training)
    return new_approval


# Approval actions are handled by the dedicated approvals module/service.

