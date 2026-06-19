from typing import Optional
from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    total_users: int
    total_incidents: int
    open_incidents: int
    high_critical_incidents: int
    open_tasks: int
    pending_approvals: int
    incomplete_trainings: int
    training_completion_rate: float
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
    review_trainings: int


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