import json
from datetime import datetime, timedelta
import random
import string

from fastapi.testclient import TestClient
from pydantic import SecretStr, EmailStr
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import UserCreate, User, UserUpdate, Subject


"""
Misc. utilities
"""


def pprint_dict(json_dict: dict) -> None:
    print(json.dumps(json_dict, indent=4, default=str))


"""
Helpers for generating random object parameters
"""


def random_lower_string(k: int = 32) -> str:
    return ''.join(random.choices(string.ascii_lowercase, k=k))


def random_digits_string(k: int = 32) -> str:
    return ''.join(random.choices(string.digits, k=k))


def random_password() -> str | SecretStr:  # typehint to silence warnings
    """To fulfill password validation of UserCreate 'password' field"""
    letters, digits = random_lower_string(16), random_digits_string(16)
    return letters + digits


def random_email() -> str | EmailStr:  # typehint to silence warnings
    return EmailStr(f'{random_lower_string()}@{random_lower_string()}.com')


def random_int(a: int = 1, b: int = 12) -> int:
    return random.randint(a, b)


def random_subject() -> Subject:
    return random.choice(list(Subject))


def utc_now() -> datetime:
    return datetime.utcnow()


def random_future_date() -> datetime:
    return datetime.utcnow() + timedelta(days=random.randint(1, 1000))


def random_accuracy() -> float:
    return random.uniform(0.01, 100.0)


"""
User/Auth
"""


def get_superuser_token_headers(client: TestClient) -> dict[str, str]:
    data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PW,
    }
    r = client.post(f"/auth/login", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def user_authentication_headers(
        *, client: TestClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}
    r = client.post(f"auth/login", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def get_user_from_token_headers(
        client: TestClient, auth_headers: dict
) -> User:
    r = client.get('/user/me', headers=auth_headers)
    response = r.json()
    return User(**response)


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
        user_in_create = UserCreate(
            email=email, password=password  # type: ignore
        )
        crud.user.create(session, obj_in=user_in_create)
    else:
        user_in_update = UserUpdate(email=email, password=password)
        crud.user.update(session, db_obj=user, obj_in=user_in_update)

    return user_authentication_headers(client=client, email=email,
                                       password=password)
