from fastapi import APIRouter,  Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tasks import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.users import RegisterRequest
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.notifications import send_notification
from app.utils.rate_limit import limiter
from app.utils.exceptions import DuplicateException

router = APIRouter(prefix="/auth", tags=["Authentication"])



@router.post(
    "/register", 
    response_model=TokenResponse, 
    status_code=201,
    responses= {
        400: {"description": "Bad request (ex: invalid syntax)"},
        409: {"description": "User with this email already exists"},
        422: {"description": "Validation error (invalid email format, short password, etc.)"},
    },
    summary="Register a new user",

)
@limiter.limit("5/minute")
def register(
    request: Request,
    credentials: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    
    - **Auth:** not required
    - **Rate limit:** 5 requests/minute
    - **Body:** `name`, `email`, `password`
    - **201:** `{ "access_token": "<jwt>", "token_type": "bearer" }` — token `sub` is the new user id
    - **409:** email already registered
    - **422:** body fails validation
    """
    existing = db.query(User).filter(User.email == credentials.email).first()
    if existing:
        raise DuplicateException("User", "email", credentials.email)
    
    user = User(
        name=credentials.name,
        email=credentials.email,
        hashed_password=hash_password(credentials.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str (user.id)})
    
    return {"access_token": token, "token_type": "bearer"}



@router.post(
    "/login",
    response_model=TokenResponse,
    responses= {
        401: {"description": "Invalid email or password "},
        422: {"description": "Validation error"},
    },
    summary="Authenticate a user and return JWT token",

)
@limiter.limit("10/minute")
def login(
    request: Request,
    credentials : LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Log in and receive an access token
    
    - **Auth:** not required
    - **Rate limit:** 10 requests/minute
    - **Body:** `email`, `password`
    - **200:** `{ "access_token": "<jwt>", "token_type": "bearer" }`
    - **401:** unknown email or wrong password (same message for both — no user enumeration)
    - **422:** body fails validation
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(data={"sub": str (user.id)})
    return {"access_token": token, "token_type": "bearer"}

