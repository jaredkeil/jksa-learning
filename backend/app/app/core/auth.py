from datetime import datetime, timedelta
from typing import Optional, MutableMapping

from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import SecretStr
from sqlmodel import Session

from app import crud
from app.core.security import verify_password
from app.models import User

JWTPayloadMapping = MutableMapping[str, (datetime | bool | str | list[str] | list[int])]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/access-token")


# oauth2_scheme = OAuth2PasswordBearer(
#     tokenUrl=f"{settings.API_V1_STR}/auth/login"
# )


def authenticate(
        *, email: str, password: SecretStr, session: Session
) -> Optional[User]:
    """
    Verify a password against the hashed password for a given email/username
    in the database.

    :param email: The email/username being authenticated
    :param password: The password to verify for the email
    :param session: The database session, used to retrieve hash
    :return: If password is correct, the User object with that email.
    If password is not correct, or email/username does not exist in database,
     returns None.
    """
    user: User = crud.user.get_by_email(session, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(*, subject: str, exp: int, key: SecretStr, algo: str) -> str:
    """
    Encode a subject into a JWT token that has some preset claims.

    :param subject: The string, such as a username, to be encoded
    :param exp: When the access token will expire
    :param key: The JWT secret key used to encode token
    :param algo: The algorithm used to encode token

    :return: A JWT token as a string
    """
    # The "exp" (expiration time) claim identifies the expiration time on
    # or after which the JWT MUST NOT be accepted for processing

    # The "iat" (issued at) claim identifies the time at which the
    # JWT was issued.

    # The "sub" (subject) claim identifies the principal that is the
    # subject of the JWT

    return jwt.encode(
        claims={
            "type": "access_token",
            "exp": datetime.utcnow()
                   + timedelta(minutes=exp),
            "iat": datetime.utcnow(),
            "sub": str(subject),
        },
        key=str(key),
        algorithm=algo,
    )
