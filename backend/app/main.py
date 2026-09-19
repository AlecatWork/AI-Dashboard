"""
Security measures:
- CORS restricted to the known frontend origins:
    * http://localhost:8501 (Streamlit)
    * http://localhost:3000 (React)
- CORS methods restricted to the HTTP methods used by the API.
- SlowAPI rate limiting:
    * Login: 10 requests/minute
    * POST/create endpoints: 20 requests/minute
    * GET/list endpoints: 60 requests/minute
- Pydantic schemas enforce input length and numeric bounds.
- Authentication is required for protected task modification endpoints.
- Application-specific exceptions return consistent JSON responses.
- Request validation errors return HTTP 422 with field information.
"""


from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.utils.exceptions import AppException

from app.database import engine, Base
from app.models import tasks as task_model
from app.routers import tasks, users, auth
from app.utils.rate_limit import limiter
from app.utils.exceptions import AppException



# Create tables
Base.metadata.create_all(bind=engine)


tags_metadata = [
    {
        "name": "Authentication",
        "description": "User registration and login. All protected endpoints require a Bearer token."

    },
    {
        "name": "Tasks",
        "description": "Task Manager API. Most endpoints require authentication."

    },
    {
        "name": "Users",
        "description": "The authenticated user's profile."

    },
]

app = FastAPI(
    title="Task Manager API",
    description="""
    A full-featured Task management API with JWT authentication. Pydantic validation, and SQLAlchemy persistence.

    ## Quick Start
    1. Register at 'POST /auth/register'
    2. Copy the 'access_token' from the response
    3. Click **Authorize** above and paste the token
    4. Start creating and managing tasks
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
)


# Rate limiting
app.state.limiter = limiter 
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)



# routers
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(auth.router)



# Application exception
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "detail": exc.detail}
    )



# Validation errors
@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": " -> ".join(str(l) for l in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"error": True, "detail": "Validation failed", "errors": errors}
    )