from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_users: int
    open_incidents: int
    closed_incidents: int
    pending_tasks: int
    tasks_under_review: int
    completed_tasks: int
    pending_approvals: int
    training_completion_rate: float
    overdue_trainings: int


class IncidentStats(BaseModel):
    by_status: dict
    by_severity: dict
    by_type: dict
    trend: list


class TaskStats(BaseModel):
    by_status: dict
    by_priority: dict
    by_assignee: dict
    trend: list


class TrainingStats(BaseModel):
    by_status: dict
    by_type: dict
    completion_rate: float
    overdue_count: int


class ApprovalStats(BaseModel):
    by_status: dict
    by_module: dict