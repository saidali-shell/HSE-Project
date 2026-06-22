from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.auth import get_current_user, require_role

router = APIRouter()


@router.get(
    "/approvals",
    response_model=List[schemas.ApprovalResponse],
    tags=["Approval Workflow"]
)
async def get_all_approvals(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_role("HSE Manager")
    ),
):
    approvals = (
        db.query(models.Approval)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return approvals


@router.get(
    "/approvals/{approval_id}",
    response_model=schemas.ApprovalResponse,
    tags=["Approval Workflow"]
)
async def get_approval_by_id(
    approval_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_role("HSE Manager")
    ),
):
    approval = (
        db.query(models.Approval)
        .filter(models.Approval.approval_id == approval_id)
        .first()
    )

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found"
        )

    return approval


@router.post(
    "/approvals",
    response_model=schemas.ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Approval Workflow"]
)
async def create_approval(
    approval_data: schemas.ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_approval = models.Approval(
        module_type=approval_data.module_type,
        reference_id=approval_data.reference_id,
        requested_by=approval_data.requested_by,
        approved_by=approval_data.approved_by,
        status=approval_data.status,
        comments=approval_data.comments
    )

    db.add(new_approval)
    db.commit()
    db.refresh(new_approval)

    return new_approval


@router.patch(
    "/approvals/{approval_id}/approve",
    response_model=schemas.ApprovalResponse,
    tags=["Approval Workflow"]
)
async def approve_approval(
    approval_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_role("HSE Manager")
    ),
):
    approval = (
        db.query(models.Approval)
        .filter(models.Approval.approval_id == approval_id)
        .first()
    )

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found"
        )

    if approval.status == "Approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approval request is already approved"
        )

    if approval.status == "Rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot approve a rejected request"
        )

    approval.status = "Approved"
    approval.approved_by = current_user.user_id

    # TASK APPROVED
    if approval.module_type == "TASK":
        task = (
            db.query(models.Task)
            .filter(models.Task.task_id == approval.reference_id)
            .first()
        )

        if task:
            task.status = "Done"
            task.reviewed_by = current_user.user_id
            task.reviewed_at = datetime.now()

            # Investigation Task -> Close Incident
            if task.title.lower() == "investigation":
                incident = (
                    db.query(models.Incident)
                    .filter(models.Incident.incident_id == task.incident_id)
                    .first()
                )

                if incident:
                    incident.status = "Closed"

    # TRAINING APPROVED
    elif approval.module_type == "TRAINING":
        training = (
            db.query(models.Training)
            .filter(models.Training.training_id == approval.reference_id)
            .first()
        )

        if training:
            training.status = "Completed"

    db.commit()
    db.refresh(approval)

    return approval


@router.patch(
    "/approvals/{approval_id}/reject",
    response_model=schemas.ApprovalResponse,
    tags=["Approval Workflow"]
)
async def reject_approval(
    approval_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_role("HSE Manager")
    ),
):
    approval = (
        db.query(models.Approval)
        .filter(models.Approval.approval_id == approval_id)
        .first()
    )

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found"
        )

    if approval.status == "Rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approval request is already rejected"
        )

    if approval.status == "Approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reject an approved request"
        )

    approval.status = "Rejected"
    approval.approved_by = current_user.user_id

    # TASK REJECTED
    if approval.module_type == "TASK":
        task = (
            db.query(models.Task)
            .filter(models.Task.task_id == approval.reference_id)
            .first()
        )

        if task:
            task.status = "In Progress"
            task.reviewed_by = current_user.user_id
            task.reviewed_at = datetime.now()

            # Investigation Task -> Incident back to Under Investigation
            if task.title.lower() == "investigation":
                incident = (
                    db.query(models.Incident)
                    .filter(models.Incident.incident_id == task.incident_id)
                    .first()
                )

                if incident:
                    incident.status = "Under Investigation"

    # TRAINING REJECTED
    elif approval.module_type == "TRAINING":
        training = (
            db.query(models.Training)
            .filter(models.Training.training_id == approval.reference_id)
            .first()
        )

        if training:
            training.status = "Incomplete"

    db.commit()
    db.refresh(approval)

    return approval