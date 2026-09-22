from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, pwd_context
from app.models import User
from app.schemas import Token, UserCreate


def register_user(db: Session, user_data: UserCreate) -> Token:
    """Register a new user and return a JWT token.

    Raises 409 if the username is already taken.
    """
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )
    db_user = User(
        username=user_data.username,
        hashed_password=pwd_context.hash(user_data.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token = create_access_token(data={"sub": user_data.username})
    return Token(access_token=access_token)


def authenticate_user(db: Session, username: str, password: str) -> Token:
    """Authenticate an existing user and return a JWT token.

    Raises 401 if credentials are invalid.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": username})
    return Token(access_token=access_token)
