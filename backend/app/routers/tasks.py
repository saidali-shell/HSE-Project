from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from typing import Optional
import uuid

from backend.app.auth import get_current_user, require_role
from backend.app.database import get_db
from backend.app.models import Task, Incident, Approval, User

router = APIRouter()

# PYDANTIC SCHEMAS

class TaskCreate(BaseModel):
    title: str
    description: str
    priority: str
    status: str = "To Do"
    assigned_to: str
    created_by: str
    incident_id: str
    due_date: date


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None


class StatusUpdate(BaseModel):
    status: str


# GET ALL TASKS (MANAGER VIEW)

@router.get("/")
def get_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager", "Admin")),
):

    tasks = db.query(Task).filter(
        Task.is_deleted == False
    ).all()

    if not tasks:
        return {
            "message": "No tasks available."
        }

    return tasks



# GET MY TASKS (EMPLOYEE VIEW)

@router.get("/my/{user_id}")
def get_my_tasks(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    tasks = db.query(Task).filter(
        Task.assigned_to == user_id,
        Task.is_deleted == False
    ).all()

    if not tasks:
        return {
            "message": "No tasks assigned to this employee."
        }

    return tasks


# GET TASK BY ID

@router.get("/{task_id}")
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    task = db.query(Task).filter(
        Task.task_id == task_id,
        Task.is_deleted == False
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task

ALLOWED_PRIORITIES = ["Low", "Medium", "High", "Urgent"]

ALLOWED_STATUSES = [
    "To Do",
    "In Progress",
    "Review",
    "Completed"
]
# CREATE TASK

@router.post("/")
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager", "Admin")),
):

    if task.priority not in ALLOWED_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail="Invalid priority. Allowed values are Low, Medium, High and Urgent."
        )

    if task.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Allowed values are To Do, In Progress, Review and Completed."
        )

    if task.due_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="Due date cannot be earlier than today's date."
        )


    new_task = Task(
        task_id=str(uuid.uuid4()),
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=task.status,
        assigned_to=task.assigned_to,
        created_by=task.created_by,
        incident_id=task.incident_id,
        due_date=task.due_date,
        is_deleted=False
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {
        "id": str(new_task.task_id),
        "message": "Task created successfully"
    }


# UPDATE TASK DETAILS (MANAGER ONLY)

@router.patch("/{task_id}")
def update_task(
    task_id: str,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager", "Admin")),
):
    if payload.priority is not None:

        if payload.priority not in ALLOWED_PRIORITIES:
            raise HTTPException(
                status_code=400,
                detail="Invalid priority. Allowed values are Low, Medium, High and Urgent."
            )
        if payload.due_date is not None:
            if payload.due_date < date.today():
                raise HTTPException(
                    status_code=400,
                    detail="Due date cannot be earlier than today's date."
                )

    task = db.query(Task).filter(
        Task.task_id == task_id,
        Task.is_deleted == False
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    if payload.title is not None:
        task.title = payload.title

    if payload.description is not None:
        task.description = payload.description

    if payload.priority is not None:
        task.priority = payload.priority

    if payload.assigned_to is not None:
        task.assigned_to = payload.assigned_to

    if payload.due_date is not None:
        task.due_date = payload.due_date

    db.commit()

    return {
        "id": str(task.task_id),
        "message": "Task updated successfully"
    }


# UPDATE TASK STATUS (assigned user or manager)

@router.patch("/{task_id}/status")
def update_status(
    task_id: str,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    task = db.query(Task).filter(
        Task.task_id == task_id,
        Task.is_deleted == False
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Employee workflow only
    valid_transitions = {
        "To Do": ["In Progress"],
        "In Progress": ["Review"],
        "Review": [],          # Employee cannot move further
        "Completed": []
    }

    if payload.status not in valid_transitions[task.status]:
        raise HTTPException(
            status_code=400,
            detail=f"Task can only move from '{task.status}' to {valid_transitions[task.status]}"
        )

    task.status = payload.status

    # Get linked incident
    incident = db.query(Incident).filter(
        Incident.incident_id == task.incident_id
    ).first()

    # To Do -> In Progress
    if payload.status == "In Progress":

        if incident:
            incident.status = "Under Investigation"

    # In Progress -> Review
    elif payload.status == "Review":

        if incident:
            incident.status = "Resolved"

        # Create approval request automatically
        approval = Approval(
            approval_id=str(uuid.uuid4()),
            module_type="TASK",
            reference_id=task.task_id,
            requested_by=task.assigned_to,
            status="Pending"
        )

        db.add(approval)

    db.commit()

    return {
        "id": str(task.task_id),
        "status": task.status,
        "message": "Task status updated successfully"
    }


# SOFT DELETE TASK

@router.delete("/{task_id}")
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager", "Admin")),
):

    task = db.query(Task).filter(
        Task.task_id == task_id,
        Task.is_deleted == False
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    task.is_deleted = True

    db.commit()

    return {
        "message": "Task deleted successfully"
    }


# TASK BOARD (MANAGER DASHBOARD VIEW)

@router.get("/board")
def task_board(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager", "Admin")),
):

    tasks = db.query(Task).filter(
        Task.is_deleted == False
    ).all()

    board = {
        "todo": [],
        "in_progress": [],
        "review": [],
        "completed": []
    }

    for task in tasks:

        item = {
            "id": str(task.task_id),
            "title": task.title
        }

        if task.status == "To Do":
            board["todo"].append(item)

        elif task.status == "In Progress":
            board["in_progress"].append(item)

        elif task.status == "Review":
            board["review"].append(item)

        elif task.status == "Completed":
            board["completed"].append(item)

    return board

# GET TASKS BY INCIDENT ID
@router.get("/incidents/{incident_id}/tasks")
def get_tasks_by_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager", "Admin")),
):

    tasks = db.query(Task).filter(
        Task.incident_id == incident_id,
        Task.is_deleted == False
    ).all()

    return tasks