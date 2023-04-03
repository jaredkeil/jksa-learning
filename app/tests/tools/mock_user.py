from fastapi.testclient import TestClient
from pydantic import EmailStr
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import UserCreate, User, UserUpdate
from app.tests.tools.mock_params import random_password


def get_user_from_token_headers(client: TestClient, auth_headers: dict) -> User:
    response = client.get("/user/me", headers=auth_headers)
    return User(**response.json())


def user_authentication_headers(
    *, client: TestClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}
    response = client.post("auth/login", data=data)
    auth_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {auth_token}"}


def get_superuser_token_headers(client: TestClient) -> dict[str, str]:
    return user_authentication_headers(
        client=client,
        email=settings.FIRST_SUPERUSER,
        password=settings.FIRST_SUPERUSER_PW,
    )


def authentication_token_from_email(
    client: TestClient, session: Session, email: str | EmailStr
) -> dict[str, str]:
    """
    Return a valid token for the user with given email.
    If the user doesn't exist it is created first.
    """
    # Even if user exists, update password, since plain-text password is not
    # stored in the database, and that is what is required for login.
    password = random_password()

    user = crud.user.get_by_email(session, email=email)
    if not user:
        user_in_create = UserCreate(email=email, password=password)
        crud.user.create(session, obj_in=user_in_create)
    else:
        user_in_update = UserUpdate(email=email, password=password)
        crud.user.update(session, db_obj=user, obj_in=user_in_update)

    return user_authentication_headers(client=client, email=email, password=password)
