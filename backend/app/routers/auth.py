from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

router = APIRouter()


@router.post("/login", response_model=schemas.TokenResponse, tags=["Authentication"])
async def login(request: Request, login_request: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    User login endpoint.
    
    Accepts email and password, returns JWT access token if credentials are valid.
    
    **Request Body:**
    - email: User email address
    - password: User password
    
    **Response:**
    - access_token: JWT token to use in Authorization header
    - token_type: Always "bearer"
    - role: User role (Admin, HSE Manager, Employee)
    """
    # Find user by email
    user = db.query(models.User).filter(models.User.email == login_request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Check if user is active
    if user.status != "Active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Verify password
    if not verify_password(login_request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.user_id), "role": user.role})
    
    return schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
    )