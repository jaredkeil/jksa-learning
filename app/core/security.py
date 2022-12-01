from passlib.context import CryptContext
from pydantic import SecretStr

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_pw: SecretStr, hashed_pw: SecretStr) -> bool:
    return PWD_CONTEXT.verify(
        plain_pw.get_secret_value(),
        hashed_pw.get_secret_value()
    )


def get_password_hash(password: SecretStr | str) -> SecretStr:
    if not isinstance(password, SecretStr):
        password = SecretStr(password)
    return SecretStr(PWD_CONTEXT.hash(password.get_secret_value()))
