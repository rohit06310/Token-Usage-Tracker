from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.token import Token
from app.core.deps import AuthenticatedUser
from app.schemas.user import UserCreate, UserResponse, ChangePasswordRequest, UserUpdate
from app.services.db import get_db

router = APIRouter()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user.
    """
    hashed_password = get_password_hash(user_in.password)
    user = User(email=user_in.email, hashed_password=hashed_password)
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, getting an access token for future requests.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: AuthenticatedUser) -> Any:
    """
    Get current user.
    """
    return current_user.user


@router.patch("/me", response_model=UserResponse, summary="Update user settings")
def update_user_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
) -> Any:
    """
    Update the current user's settings.
    """
    user = current_user.user
    if payload.preferred_currency is not None:
        user.preferred_currency = payload.preferred_currency

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password", summary="Change user password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
) -> Any:
    """
    Change the current user's password.
    """
    user = current_user.user

    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password.",
        )

    user.hashed_password = get_password_hash(payload.new_password)
    db.add(user)
    db.commit()

    return {"message": "Password updated successfully."}
