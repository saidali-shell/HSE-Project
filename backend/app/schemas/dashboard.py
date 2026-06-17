from typing import Optional
from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    total_users: int
    open_incidents: int
    closed_incidents: int
    under_investigation: int
    open_tasks: int
    pending_tasks: int
    tasks_under_review: int
    completed_tasks: int
    pending_approvals: int
    completed_trainings: int
    incomplete_trainings: int
    training_completion_rate: float
    overdue_trainings: int
    days_since_last_incident: Optional[int] = None


class IncidentChartResponse(BaseModel):
    low: int
    medium: int
    high: int
    critical: int


class TaskStatsResponse(BaseModel):
    total_tasks: int
    todo_tasks: int
    in_progress_tasks: int
    review_tasks: int
    completed_tasks: int


class TrainingStatsResponse(BaseModel):
    total_trainings: int
    completed_trainings: int
    incomplete_trainings: int


class ApprovalStatsResponse(BaseModel):
    total_approvals: int
    pending_approvals: int
    approved_approvals: int
    rejected_approvals: int


class EmployeeDashboardResponse(BaseModel):
    my_tasks: int
    my_pending_tasks: int
    my_completed_tasks: int
    my_trainings: int
    my_completed_trainings: int
    my_incomplete_trainings: int
    my_pending_approvals: int