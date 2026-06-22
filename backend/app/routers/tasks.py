import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user, require_role
from backend.app.database import get_db
from backend.app.models import Task, Incident, Approval, User
from backend.app.schemas.task import TaskCreate, TaskUpdate, StatusUpdate, TaskResponse

router = APIRouter()


@router.get("/", response_model=List[TaskResponse])
def get_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager")),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=100),
):
    tasks = db.query(Task).filter(
        Task.is_deleted == False
    ).offset((page - 1) * size).limit(size).all()

    return tasks


@router.get("/my", response_model=List[TaskResponse])
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=100),
):
    tasks = db.query(Task).filter(
        Task.assigned_to == current_user.user_id,
        Task.is_deleted == False
    ).offset((page - 1) * size).limit(size).all()

    return tasks


@router.get("/overdue", response_model=List[TaskResponse])
def get_overdue_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager")),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=100),
):
    today = date.today()
    tasks = db.query(Task).filter(
        Task.due_date < today,
        Task.status != "Done",
        Task.is_deleted == False
    ).offset((page - 1) * size).limit(size).all()

    return tasks


@router.get("/board")
def task_board(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager")),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=100),
):
    tasks = db.query(Task).filter(
        Task.is_deleted == False
    ).offset((page - 1) * size).limit(size).all()

    board = {
        "todo": [],
        "in_progress": [],
        "review": [],
        "done": []
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
        elif task.status == "Done":
            board["done"].append(item)

    return board


@router.get("/incidents/{incident_id}/tasks", response_model=List[TaskResponse])
def get_tasks_by_incident(
    incident_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager")),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=100),
):
    tasks = db.query(Task).filter(
        Task.incident_id == incident_id,
        Task.is_deleted == False
    ).offset((page - 1) * size).limit(size).all()

    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: uuid.UUID,
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

    if current_user.role not in ["HSE Manager", "Admin"] and task.assigned_to != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to view this task."
        )

    return task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager")),
):
    if task.due_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="Due date cannot be earlier than today's date."
        )

    incident = db.query(Incident).filter(
        Incident.incident_id == task.incident_id
    ).first()

    if not incident:
        raise HTTPException(
            status_code=400,
            detail="Invalid incident ID. Incident not found."
        )

    assignee = db.query(User).filter(
        User.user_id == task.assigned_to,
        User.status == "Active"
    ).first()

    if not assignee:
        raise HTTPException(
            status_code=400,
            detail="Assigned employee not found or inactive."
        )

    if assignee.role != "Employee":
        raise HTTPException(
            status_code=400,
            detail="Task must be assigned to a user with the Employee role."
        )

    new_task = Task(
        task_id=uuid.uuid4(),
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=task.status,
        assigned_to=task.assigned_to,
        created_by=current_user.user_id,
        incident_id=task.incident_id,
        due_date=task.due_date,
        is_deleted=False
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager")),
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

    update_data = payload.model_dump(exclude_unset=True)

    if "priority" in update_data and update_data["priority"] not in ["Low", "Medium", "High", "Urgent"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid priority. Allowed values are Low, Medium, High and Urgent."
        )

    if "status" in update_data and update_data["status"] not in ["To Do", "In Progress", "Review", "Done"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Allowed values are To Do, In Progress, Review and Done."
        )

    if "due_date" in update_data and update_data["due_date"] is not None:
        if update_data["due_date"] < date.today():
            raise HTTPException(
                status_code=400,
                detail="Due date cannot be earlier than today's date."
            )

    if "assigned_to" in update_data and update_data["assigned_to"] is not None:
        assignee = db.query(User).filter(
            User.user_id == update_data["assigned_to"],
            User.status == "Active"
        ).first()
        if not assignee:
            raise HTTPException(
                status_code=400,
                detail="Assigned employee not found or inactive."
            )
        if assignee.role != "Employee":
            raise HTTPException(
                status_code=400,
                detail="Task must be assigned to a user with the Employee role."
            )

    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)

    return task


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_status(
    task_id: uuid.UUID,
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

    is_manager = current_user.role in ["HSE Manager", "Admin"]
    is_task_assigned_to_user = task.assigned_to == current_user.user_id

    if not (is_manager or is_task_assigned_to_user):
        raise HTTPException(
            status_code=403,
            detail="You can only update status for tasks assigned to you"
        )

    valid_transitions = {
        "To Do": ["In Progress"],
        "In Progress": ["Review"],
        "Review": [],
        "Done": []
    }

    if payload.status not in valid_transitions.get(task.status, []):
        if not is_manager:
            raise HTTPException(
                status_code=400,
                detail=f"Task can only move from '{task.status}' to {valid_transitions.get(task.status, [])}"
            )

    task.status = payload.status

    incident = db.query(Incident).filter(
        Incident.incident_id == task.incident_id
    ).first()

    if payload.status == "In Progress" and incident:
        incident.status = "Under Investigation"

    elif payload.status == "Review" and incident:
        incident.status = "Resolved"

        approval = Approval(
            approval_id=uuid.uuid4(),
            module_type="TASK",
            reference_id=task.task_id,
            requested_by=task.assigned_to,
            status="Pending"
        )
        db.add(approval)

    db.commit()
    db.refresh(task)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("HSE Manager")),
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

    return None