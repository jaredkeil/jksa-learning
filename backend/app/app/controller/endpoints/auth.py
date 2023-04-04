from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import SecretStr
from sqlalchemy.orm.session import Session

from app import crud
from app.core.auth import authenticate, create_access_token
from app.core.config import Settings
from app.deps import get_session, get_settings
from app.models import UserRead, UserCreate

router = APIRouter()


# @router.post("/login", response_model=deps.Token)
@router.post("/login")
def login(
    session: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
    settings: Settings = Depends(get_settings),
) -> Any:
    """
    Get the JWT for a user with data from OAuth2 request form body.
    """
    user = authenticate(
        email=form_data.username,
        password=SecretStr(form_data.password),
        session=session,
    )
    if not user:
        raise HTTPException(400, "Incorrect username or password")
    return {
        "access_token": create_access_token(
            subject=str(user.id),
            exp=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            key=settings.JWT_SECRET,
            algo=settings.ALGORITHM,
        ),
        "token_type": "bearer",
        "user": UserRead.from_orm(user),
    }


@router.post("/signup", response_model=UserRead, status_code=201)
def create_user_signup(
    *,
    session: Session = Depends(get_session),
    user_in: UserCreate,
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    if crud.user.get_by_email(session, email=user_in.email):
        raise HTTPException(400, "A user with this email already exists.")
    return crud.user.create(session, obj_in=user_in)
