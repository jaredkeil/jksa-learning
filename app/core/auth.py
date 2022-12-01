from typing import Optional, MutableMapping
from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordBearer
from pydantic import SecretStr
from sqlmodel import Session
from jose import jwt

from app import crud
from app.core.config import settings
from app.core.security import verify_password
from app.models import User

JWTPayloadMapping = MutableMapping[
    str,
    (datetime | bool | str | list[str] | list[int])
]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/access-token")

# oauth2_scheme = OAuth2PasswordBearer(
#     tokenUrl=f"{settings.API_V1_STR}/auth/login"
# )


def authenticate(*, email: str, password: SecretStr, session: Session
                 ) -> Optional[User]:
    user: User = crud.user.get_by_email(session, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(*, sub: str) -> str:
    return _create_token(
        token_type="access_token",
        lifetime=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        sub=sub,
    )


def _create_token(token_type: str, lifetime: timedelta, sub: str) -> str:
    # https://datatracker.ietf.org/doc/html/rfc7519#section-4.1.3
    # The "exp" (expiration time) claim identifies the expiration time on
    # or after which the JWT MUST NOT be accepted for processing

    # The "iat" (issued at) claim identifies the time at which the
    # JWT was issued.

    # The "sub" (subject) claim identifies the principal that is the
    # subject of the JWT

    payload = {
        'type': token_type,
        'exp': datetime.utcnow() + lifetime,
        'iat': datetime.utcnow(),
        'sub': str(sub)
    }
    return jwt.encode(payload, settings.JWT_SECRET, settings.ALGORITHM)
