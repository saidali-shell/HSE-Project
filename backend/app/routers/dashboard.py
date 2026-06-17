import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from backend.app.database import get_db
from backend.app.models import User, Incident, Task, Approval, Training
from backend.app.schemas.dashboard import (
    DashboardSummaryResponse,
    IncidentChartResponse,
    TaskStatsResponse,
    TrainingStatsResponse,
    ApprovalStatsResponse,
    EmployeeDashboardResponse,
)

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):

    # Users
    total_users = db.query(User).count()

    # Incidents
    open_incidents = db.query(Incident).filter(Incident.status != "Closed").count()
    closed_incidents = db.query(Incident).filter(Incident.status == "Closed").count()
    under_investigation = db.query(Incident).filter(Incident.status == "Under Investigation").count()

    # Tasks
    open_tasks = db.query(Task).filter(Task.status != "Done", Task.is_deleted == False).count()
    pending_tasks = db.query(Task).filter(Task.status == "To Do", Task.is_deleted == False).count()
    tasks_under_review = db.query(Task).filter(Task.status == "Review", Task.is_deleted == False).count()
    completed_tasks = db.query(Task).filter(Task.status == "Done", Task.is_deleted == False).count()

    # Approvals
    pending_approvals = db.query(Approval).filter(Approval.status == "Pending").count()

    # Trainings
    total_trainings = db.query(Training).count()
    completed_trainings = db.query(Training).filter(Training.status == "Completed").count()
    incomplete_trainings = db.query(Training).filter(Training.status == "Incomplete").count()
    overdue_trainings = db.query(Training).filter(
        Training.status == "Incomplete",
        Training.end_date < date.today()
    ).count()
    training_completion_rate = round(
        (completed_trainings / total_trainings * 100) if total_trainings > 0 else 0.0, 2
    )

    # Days since last incident
    latest_incident = db.query(func.max(Incident.incident_date)).scalar()
    days_since_last_incident = (date.today() - latest_incident).days if latest_incident else None

    return {
        "total_users": total_users,
        "open_incidents": open_incidents,
        "closed_incidents": closed_incidents,
        "under_investigation": under_investigation,
        "open_tasks": open_tasks,
        "pending_tasks": pending_tasks,
        "tasks_under_review": tasks_under_review,
        "completed_tasks": completed_tasks,
        "pending_approvals": pending_approvals,
        "completed_trainings": completed_trainings,
        "incomplete_trainings": incomplete_trainings,
        "training_completion_rate": training_completion_rate,
        "overdue_trainings": overdue_trainings,
        "days_since_last_incident": days_since_last_incident,
    }


@router.get("/charts/incidents", response_model=IncidentChartResponse)
def get_incident_chart(db: Session = Depends(get_db)):

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
def get_task_stats(db: Session = Depends(get_db)):

    result = db.query(
        func.count(Task.task_id).label("total"),
        func.count(case((Task.status == "To Do", Task.task_id))).label("todo"),
        func.count(case((Task.status == "In Progress", Task.task_id))).label("in_progress"),
        func.count(case((Task.status == "Review", Task.task_id))).label("review"),
        func.count(case((Task.status == "Done", Task.task_id))).label("done"),
    ).filter(Task.is_deleted == False).one()

    return {
        "total_tasks": result.total,
        "todo_tasks": result.todo,
        "in_progress_tasks": result.in_progress,
        "review_tasks": result.review,
        "completed_tasks": result.done,
    }


@router.get("/trainings", response_model=TrainingStatsResponse)
def get_training_stats(db: Session = Depends(get_db)):

    total_trainings = db.query(Training).count()
    completed_trainings = db.query(Training).filter(Training.status == "Completed").count()
    incomplete_trainings = db.query(Training).filter(Training.status == "Incomplete").count()

    return {
        "total_trainings": total_trainings,
        "completed_trainings": completed_trainings,
        "incomplete_trainings": incomplete_trainings,
    }


@router.get("/approvals", response_model=ApprovalStatsResponse)
def get_approval_stats(db: Session = Depends(get_db)):

    return {
        "total_approvals": db.query(Approval).count(),
        "pending_approvals": db.query(Approval).filter(Approval.status == "Pending").count(),
        "approved_approvals": db.query(Approval).filter(Approval.status == "Approved").count(),
        "rejected_approvals": db.query(Approval).filter(Approval.status == "Rejected").count(),
    }


@router.get("/employee/{user_id}", response_model=EmployeeDashboardResponse)
def get_employee_dashboard(user_id: str, db: Session = Depends(get_db)):

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
        "my_incomplete_trainings": db.query(Training).filter(Training.assigned_to == uid, Training.status == "Incomplete").count(),
        "my_pending_approvals": db.query(Approval).filter(Approval.requested_by == uid, Approval.status == "Pending").count(),
    }