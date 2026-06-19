import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from backend.app.database import get_db
from backend.app.models import User, Incident, Task, Approval, Training
from backend.app.auth import get_current_user, require_role
from backend.app.schemas.dashboard import (
    DashboardSummaryResponse,
    IncidentChartResponse,
    TaskStatsResponse,
    TrainingStatsResponse,
    ApprovalStatsResponse,
    EmployeeDashboardResponse,
)

router = APIRouter()


VALID_PERIODS = {"all", "month", "quarter", "year"}

def get_date_filter(period: str):
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period. Must be one of: {', '.join(VALID_PERIODS)}"
        )
    today = date.today()
    if period == "month":
        return date(today.year, today.month, 1)
    elif period == "quarter":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        return date(today.year, quarter_start_month, 1)
    elif period == "year":
        return date(today.year, 1, 1)
    return None


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    period: str = "all",
    current_user: User = Depends(require_role("HSE Manager"))
):
    start_date = get_date_filter(period)

    # Users
    total_users = db.query(User).count()

    # Incidents — live counts (no filter)
    total_incidents = db.query(Incident).count()
    open_incidents = db.query(Incident).filter(Incident.status != "Closed").count()
    high_critical_incidents = db.query(Incident).filter(
        Incident.severity.in_(["High", "Critical"]),
        Incident.status != "Closed"
    ).count()

    # Tasks — live counts (no filter)
    open_tasks = db.query(Task).filter(
        Task.status != "Done",
        Task.is_deleted == False
    ).count()

    # Approvals — live counts (no filter)
    pending_approvals = db.query(Approval).filter(Approval.status == "Pending").count()

    # Trainings — live counts (no filter)
    incomplete_trainings = db.query(Training).filter(
        Training.status.in_(["Incomplete", "Review"])
    ).count()

    # Days since last incident — always latest
    latest_incident = db.query(func.max(Incident.incident_date)).scalar()
    days_since_last_incident = (date.today() - latest_incident).days if latest_incident else None

    # Cumulative fields — period filter applied
    training_q = db.query(Training)

    if start_date:
        training_q = training_q.filter(Training.created_at >= start_date)

    total_trainings = training_q.count()
    completed_trainings = training_q.filter(Training.status == "Completed").count()
    training_completion_rate = round(
        (completed_trainings / total_trainings * 100) if total_trainings > 0 else 0.0, 2
    )

    return {
        "total_users": total_users,
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
        "high_critical_incidents": high_critical_incidents,
        "open_tasks": open_tasks,
        "pending_approvals": pending_approvals,
        "incomplete_trainings": incomplete_trainings,
        "training_completion_rate": training_completion_rate,
        "days_since_last_incident": days_since_last_incident,
    }


@router.get("/charts/incidents", response_model=IncidentChartResponse)
def get_incident_chart(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager"))
):
    result = db.query(
        func.count(case((Incident.severity == "Low", 1))).label("low"),
        func.count(case((Incident.severity == "Medium", 1))).label("medium"),
        func.count(case((Incident.severity == "High", 1))).label("high"),
        func.count(case((Incident.severity == "Critical", 1))).label("critical"),
    ).one()

    return {
        "low": result.low,
        "medium": result.medium,
        "high": result.high,
        "critical": result.critical,
    }


@router.get("/tasks", response_model=TaskStatsResponse)
def get_task_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager"))
):
    result = db.query(
        func.count(Task.task_id).label("total"),
        func.count(case((Task.status == "To Do", Task.task_id))).label("todo"),
        func.count(case((Task.status == "In Progress", Task.task_id))).label("in_progress"),
        func.count(case((Task.status == "Review", Task.task_id))).label("review"),
        func.count(case((Task.status == "Done", Task.task_id))).label("completed"),
    ).filter(Task.is_deleted == False).one()

    return {
        "total_tasks": result.total,
        "todo_tasks": result.todo,
        "in_progress_tasks": result.in_progress,
        "review_tasks": result.review,
        "completed_tasks": result.completed,
    }


@router.get("/trainings", response_model=TrainingStatsResponse)
def get_training_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager"))
):
    total_trainings = db.query(Training).count()
    completed_trainings = db.query(Training).filter(Training.status == "Completed").count()
    incomplete_trainings = db.query(Training).filter(Training.status == "Incomplete").count()
    review_trainings = db.query(Training).filter(Training.status == "Review").count()

    return {
        "total_trainings": total_trainings,
        "completed_trainings": completed_trainings,
        "incomplete_trainings": incomplete_trainings,
        "review_trainings": review_trainings,
    }


@router.get("/approvals", response_model=ApprovalStatsResponse)
def get_approval_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager"))
):
    return {
        "total_approvals": db.query(Approval).count(),
        "pending_approvals": db.query(Approval).filter(Approval.status == "Pending").count(),
        "approved_approvals": db.query(Approval).filter(Approval.status == "Approved").count(),
        "rejected_approvals": db.query(Approval).filter(Approval.status == "Rejected").count(),
    }


@router.get("/employee/{user_id}", response_model=EmployeeDashboardResponse)
def get_employee_dashboard(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Employee"))
):
    if str(current_user.user_id) != user_id:
        raise HTTPException(
            status_code=403,
            detail="Employees can only view their own dashboard"
        )

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    return {
        "my_tasks": db.query(Task).filter(Task.assigned_to == uid, Task.is_deleted == False).count(),
        "my_pending_tasks": db.query(Task).filter(Task.assigned_to == uid, Task.status != "Done", Task.is_deleted == False).count(),
        "my_completed_tasks": db.query(Task).filter(Task.assigned_to == uid, Task.status == "Done", Task.is_deleted == False).count(),
        "my_trainings": db.query(Training).filter(Training.assigned_to == uid).count(),
        "my_completed_trainings": db.query(Training).filter(Training.assigned_to == uid, Training.status == "Completed").count(),
        "my_incomplete_trainings": db.query(Training).filter(Training.assigned_to == uid, Training.status.in_(["Incomplete", "Review"])).count(),
        "my_pending_approvals": db.query(Approval).filter(Approval.requested_by == uid, Approval.status == "Pending").count(),
    }