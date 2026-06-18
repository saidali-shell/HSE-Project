from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List
import uuid

from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user,
    require_role,
)

router = APIRouter()


@router.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, tags=["User Management"])
async def create_user(
    user_create: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Admin")),
):
    """
    Create a new user.
    
    Only Admin users can create new users.
    
    **Request Body:**
    - full_name: User's full name (2-150 characters)
    - email: Unique email address
    - password: Password (minimum 6 characters)
    - phone_number: Optional phone number (10 digits)
    - role: User role (Admin, HSE Manager, Employee) - defaults to Employee
    - status: User status (Active, Inactive) - defaults to Active
    
    **Response:**
    - Returns the created user details
    """
    # Enforce single Admin
    if user_create.role == "Admin":
        existing_admin = db.query(models.User).filter(models.User.role == "Admin").first()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin user already exists. Only one Admin allowed."
            )

    # Enforce single HSE Manager
    if user_create.role == "HSE Manager":
        existing_hse = db.query(models.User).filter(models.User.role == "HSE Manager").first()
        if existing_hse:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="HSE Manager user already exists. Only one HSE Manager allowed."
            )

    # Check if email already exists
    existing_user = db.query(models.User).filter(models.User.email == user_create.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Hash the password (catch bcrypt length errors and return 400)
    try:
        hashed_password = hash_password(user_create.password)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    
    # Create new user
    new_user = models.User(
        user_id=uuid.uuid4(),
        full_name=user_create.full_name,
        email=user_create.email,
        password_hash=hashed_password,
        phone_number=user_create.phone_number,
        role=user_create.role,
        status=user_create.status,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.get("/users", response_model=List[schemas.UserResponse], tags=["User Management"])
async def get_all_users(
    search: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Admin", "HSE Manager")),
):
    """
    Retrieve all users with optional search and pagination.
    
    **Query Parameters:**
    - search: Optional search term to filter by full_name or email (case-insensitive, partial match)
    - skip: Number of users to skip (default: 0)
    - limit: Maximum number of users to return (default: 100)
    
    **Response:**
    - Returns a list of matching users
    """
    query = db.query(models.User)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                models.User.full_name.ilike(search_pattern),
                models.User.email.ilike(search_pattern)
            )
        )
    
    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=schemas.UserResponse, tags=["User Management"])
async def get_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Retrieve a specific user by ID.
    
    **Path Parameters:**
    - user_id: UUID of the user
    
    **Response:**
    - Returns user details including name, email, role, and status
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    
    user = db.query(models.User).filter(models.User.user_id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Authorization: Admin and HSE Manager can view any user, Employee can only view own profile
    if current_user.role == "Employee" and current_user.user_id != user_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view this user"
        )
    
    return user


@router.put("/users/{user_id}", response_model=schemas.UserResponse, tags=["User Management"])
async def update_user(
    user_id: str,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Admin")),
):
    """
    Update user details.
    
    Only Admin users can update other users' details.
    
    **Path Parameters:**
    - user_id: UUID of the user to update
    
    **Request Body:**
    - full_name: Optional new full name
    - email: Optional new email address
    - phone_number: Optional new phone number
    - role: Optional new role
    - status: Optional new status
    
    **Response:**
    - Returns updated user details
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    
    user = db.query(models.User).filter(models.User.user_id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if new email is already taken by another user
    if user_update.email and user_update.email != user.email:
        existing_user = db.query(models.User).filter(
            and_(
                models.User.email == user_update.email,
                models.User.user_id != user_uuid
            )
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    # Update user fields
    if user_update.full_name:
        user.full_name = user_update.full_name
    if user_update.email:
        user.email = user_update.email
    if user_update.phone_number:
        user.phone_number = user_update.phone_number
    if user_update.role:
        user.role = user_update.role
    if user_update.status:
        user.status = user_update.status
    
    db.commit()
    db.refresh(user)
    
    return user


@router.patch("/users/{user_id}/status", response_model=schemas.UserResponse, tags=["User Management"])
async def update_user_status(
    user_id: str,
    status_update: schemas.UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Admin")),
):
    """
    Update user status (Activate/Deactivate).
    
    Only Admin users can change user status.
    
    **Path Parameters:**
    - user_id: UUID of the user
    
    **Request Body:**
    - status: New status (Active or Inactive)
    
    **Response:**
    - Returns updated user details
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    
    user = db.query(models.User).filter(models.User.user_id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.status = status_update.status
    db.commit()
    db.refresh(user)
    
    return user


@router.patch("/users/{user_id}/reset-password", status_code=status.HTTP_200_OK, tags=["User Management"])
async def reset_password(
    user_id: str,
    password_reset: schemas.PasswordReset,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Admin")),
):
    """
    Reset user password.
    
    Only Admin users can reset other users' passwords.
    
    **Path Parameters:**
    - user_id: UUID of the user
    
    **Request Body:**
    - new_password: New password (minimum 6 characters)
    
    **Response:**
    - Returns success message
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    
    user = db.query(models.User).filter(models.User.user_id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Hash and update password
    user.password_hash = hash_password(password_reset.new_password)
    db.commit()
    
    return {"message": "Password reset successfully"}