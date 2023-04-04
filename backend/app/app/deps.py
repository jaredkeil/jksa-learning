from functools import lru_cache
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status, Query
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlmodel import Session

from .core.auth import oauth2_scheme
from .core.config import Settings
from .database import engine
from .models import User, Role


@lru_cache()
def get_settings():
    return Settings()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class BatchQueryParams(BaseModel):
    q: Optional[str] = Query(default="")
    skip: Optional[int] = Query(default=0)
    limit: Optional[int] = Query(default=5000)


def get_session() -> Generator:
    with Session(engine) as session:
        yield session


async def get_current_user(
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token=token,
            key=str(settings.JWT_SECRET),
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False},
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = session.get(User, token_data.username)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(400, "The user doesn't have enough privileges")
    return current_user


def get_current_teacher(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.role == Role.teacher:
        raise HTTPException(400, "The user is not a teacher")
    return current_user


def get_current_student(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.role == Role.student:
        raise HTTPException(400, "The user is not a student")
    return current_user
