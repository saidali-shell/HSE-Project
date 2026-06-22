# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app import models  # noqa: F401  (ensures models are imported for SQLAlchemy metadata)
from backend.app.database import engine  # noqa: F401  (creates DB engine)
from backend.app.core.rate_limit import limiter

# Import routers
from backend.app.routers import auth, users, incidents,tasks , dashboard, trainings, approval

app = FastAPI(
    title="HSE Management API",
    description="A FastAPI service for users, incidents, tasks, trainings and approvals.",
    version="0.1.0",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom validation error handler - returns user-friendly messages
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        message = error["msg"]
        
        # Make messages more user-friendly
        if "field required" in message.lower():
            message = f"{field} is required"
        elif "value is not a valid email" in message.lower():
            message = "Invalid email format"
        elif "ensure this value has at least" in message.lower():
            message = f"{field} is too short"
        elif "ensure this value has at most" in message.lower():
            message = f"{field} is too long"
        elif "value is not a valid enumeration member" in message.lower():
            message = f"Invalid {field} value"
        
        # Strip Pydantic "Value error, " prefix
        if message.startswith("Value error, "):
            message = message[len("Value error, "):]
        errors.append({"field": field, "message": message})
    
    return JSONResponse(
        status_code=400,
        content={"detail": "Validation failed", "errors": errors}
    )

# Startup DB check (dev-friendly)
@app.on_event("startup")
async def startup_event():
    from backend.app import models
    from backend.app.database import engine
    try:
        # quick DB connectivity test
        conn = engine.connect()
        conn.close()
    except Exception as e:
        # Log and raise a clear error so startup fails loudly
        import logging
        logging.error("Database connection failed during startup: %s", e)
        raise


@app.get("/", tags=["health"])
async def read_root():
    """
    Simple health-check endpoint.
    Returns a friendly message so you know the API is up.
    """
    return {"msg": "HSE Management API is running 🚀"}


# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["User Management"])
app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["Incidents"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(approval.router, prefix="/api/v1", tags=["Approval Workflow"])
app.include_router(trainings.router, prefix="/api/v1/trainings", tags=["Training Management"])  # Adjust as needed for other routers
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
