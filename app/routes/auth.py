from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import Token, UserCreate
from app.services.auth_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)) -> Token:
    """Register a new user and return a JWT token."""
    return register_user(db, user)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate an existing user and return a JWT token."""
    return authenticate_user(db, form_data.username, form_data.password)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> dict:
    """Return the current authenticated user."""
    return {"username": current_user.username}
