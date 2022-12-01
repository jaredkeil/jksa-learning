from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import SecretStr
from sqlalchemy.orm.session import Session

from app import deps, crud
from app.models import UserRead, UserCreate
from app.core.auth import authenticate, create_access_token

router = APIRouter()


@router.post("/login/access-token", response_model=deps.Token)
def login(session: Session = Depends(deps.get_session),
          form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    Get the JWT for a user with data from OAuth2 request form body.
    """
    user = authenticate(email=form_data.username,
                        password=SecretStr(form_data.password),
                        session=session)
    if not user:
        raise HTTPException(400, 'Incorrect username or password')
    return {'access_token': create_access_token(sub=str(user.id)),
            'token_type': 'bearer'}


@router.post("/signup", response_model=UserRead, status_code=201)
def create_user_signup(*, session: Session = Depends(deps.get_session),
                       user_in: UserCreate,) -> Any:
    """
    Create new user without the need to be logged in.
    """
    if crud.user.get_by_email(session, email=user_in.email):
        raise HTTPException(
                400, 'The user with this email already exists in the system'
        )
    return crud.user.create(session, obj_in=user_in)
