"""
Helpers for generating random object parameters
"""
import random
import string
from datetime import datetime, timedelta

from pydantic import SecretStr, EmailStr

from app.models import Subject


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


def local_today() -> datetime:
    return datetime.today()


def random_future_date() -> datetime:
    return datetime.utcnow() + timedelta(days=random.randint(1, 1000))


def random_accuracy() -> float:
    return random.uniform(0.01, 100.0)
