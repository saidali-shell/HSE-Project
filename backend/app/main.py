# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.app import models  # noqa: F401  (ensures models are imported for SQLAlchemy metadata)
from backend.app.database import engine  # noqa: F401  (creates DB engine)

# Import routers
from backend.app.routers import auth, users,trainings  # Add other routers as needed            

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

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
app.include_router(trainings.router, prefix="/api/v1/trainings", tags=["Training Management"])  # Adjust as needed for other routers