import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

VALID_ROLES = {"Admin", "HSE Manager", "Employee"}
VALID_STATUSES = {"Active", "Inactive"}


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
            cleaned = "".join(c for c in value if c.isdigit())
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


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=72, description="Password must be at least 6 characters long and at most 72 characters")

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        b = value.encode("utf-8")
        if len(b) > 72:
            raise ValueError("Password must be at most 72 bytes when UTF-8 encoded; choose a shorter password")
        return value


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
            cleaned = "".join(c for c in value if c.isdigit())
            if len(cleaned) == 12 and cleaned.startswith("91"):
                cleaned = cleaned[2:]
            if len(cleaned) != 10:
                raise ValueError("Phone number must be a valid 10-digit number")
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


class UserStatusUpdate(BaseModel):
    status: str = Field(..., description="New status (Active, Inactive)")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return value


class PasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6, description="New password must be at least 6 characters long")


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