import uuid
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator

# Valid Enum values for roles and statuses
VALID_ROLES = {"Admin", "HSE Manager", "Employee"}
VALID_STATUSES = {"Active", "Inactive"}

# Base Schema for User properties
class UserBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150, description="Full name of the user")
    email: EmailStr = Field(..., description="Unique email address of the user")
    phone_number: Optional[str] = Field(None, max_length=20, description="Optional phone number of the user (exactly 10 digits)")
    role: str = Field("Employee", description="Role of the user (Admin, HSE Manager, Employee)")
    status: str = Field("Active", description="Status of the user (Active, Inactive)")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            # Strip spaces, dashes, parentheses, or +
            cleaned = "".join(c for c in value if c.isdigit())
            
            # If the user included the Indian country code (e.g. 919876543210), strip it
            if len(cleaned) == 12 and cleaned.startswith("91"):
                cleaned = cleaned[2:]
                
            if len(cleaned) != 10:
                raise ValueError("Phone number must be a valid 10-digit number")
            return cleaned
        return value

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in VALID_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(VALID_ROLES)}")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return value

# Schema for creating a user
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters long")

# Schema for updating user details
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    role: Optional[str] = None
    status: Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            # Strip spaces, dashes, parentheses, or +
            cleaned = "".join(c for c in value if c.isdigit())
            
            # If the user included the Indian country code (e.g. 919876543210), strip it
            if len(cleaned) == 12 and cleaned.startswith("91"):
                cleaned = cleaned[2:]
                
            if len(cleaned) != 10:
                raise ValueError("Phone number must be a valid 10-digit Indian mobile number")
            return cleaned
        return value

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in VALID_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(VALID_ROLES)}")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return value

# Schema for updating user status
class UserStatusUpdate(BaseModel):
    status: str = Field(..., description="New status (Active, Inactive)")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return value

# Schema for resetting passwords
class PasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6, description="New password must be at least 6 characters long")

# Schema for authentication / login requests
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Schema for returning token response
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str

# Schema for returning safe User profiles (excluding password hashes)
class UserResponse(BaseModel):
    user_id: uuid.UUID
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schemas for Training module
class TrainingBase(BaseModel):
    incident_id: Optional[uuid.UUID] = None
    title: str = Field(..., max_length=255)
    training_type: str = Field(..., max_length=100)
    description: str
    instructor: str = Field(..., max_length=255)
    assigned_to: uuid.UUID
    status: Literal["Completed", "Incomplete"] = "Incomplete"
    start_date: datetime
    end_date: datetime

class TrainingCreate(TrainingBase):
    pass

class TrainingUpdate(BaseModel):
    title: Optional[str] = None
    training_type: Optional[str] = None
    description: Optional[str] = None
    instructor: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    status: Optional[Literal["Completed", "Incomplete"]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class TrainingResponse(TrainingBase):
    training_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schemas for Incident module
class IncidentBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    incident_type: str = Field(..., max_length=100)
    severity: Literal["Low", "Medium", "High", "Critical"]
    location: str
    proof_image_path: Optional[str] = None
    incident_date: datetime
    status: Literal["Reported", "Under Investigation", "Resolved", "Closed"] = "Reported"
    assigned_to: Optional[uuid.UUID] = None

class IncidentCreate(IncidentBase):
    reported_by: uuid.UUID

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    incident_type: Optional[str] = None
    severity: Optional[Literal["Low", "Medium", "High", "Critical"]] = None
    location: Optional[str] = None
    proof_image_path: Optional[str] = None
    incident_date: Optional[datetime] = None
    status: Optional[Literal["Reported", "Under Investigation", "Resolved", "Closed"]] = None
    assigned_to: Optional[uuid.UUID] = None

class IncidentResponse(IncidentBase):
    incident_id: uuid.UUID
    reported_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schemas for Task module
class TaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    priority: Literal["Low", "Medium", "High", "Urgent"] = "Medium"
    status: Literal["To Do", "In Progress", "Review", "Done"] = "To Do"
    due_date: datetime
    is_deleted: bool = False

class TaskCreate(TaskBase):
    assigned_to: uuid.UUID
    created_by: uuid.UUID
    incident_id: Optional[uuid.UUID] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Literal["Low", "Medium", "High", "Urgent"]] = None
    status: Optional[Literal["To Do", "In Progress", "Review", "Done"]] = None
    assigned_to: Optional[uuid.UUID] = None
    created_by: Optional[uuid.UUID] = None
    incident_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    is_deleted: Optional[bool] = None

class TaskResponse(TaskBase):
    task_id: uuid.UUID
    assigned_to: uuid.UUID
    created_by: uuid.UUID
    incident_id: Optional[uuid.UUID] = None
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schemas for Approval module
class ApprovalBase(BaseModel):
    module_type: Literal["TASK", "TRAINING"]
    reference_id: uuid.UUID
    status: Literal["Pending", "Approved", "Rejected"] = "Pending"
    comments: Optional[str] = None

class ApprovalCreate(ApprovalBase):
    requested_by: uuid.UUID
    approved_by: Optional[uuid.UUID] = None

class ApprovalUpdate(BaseModel):
    status: Optional[Literal["Pending", "Approved", "Rejected"]] = None
    comments: Optional[str] = None
    approved_by: Optional[uuid.UUID] = None

class ApprovalResponse(ApprovalBase):
    approval_id: uuid.UUID
    requested_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

