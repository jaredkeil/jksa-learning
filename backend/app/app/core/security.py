from passlib.context import CryptContext
from pydantic import SecretStr

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: SecretStr, hashed_password: SecretStr) -> bool:
    """
    Verify a plain text password against a hash, based on the app's
    CryptoContext algorithm.
    """
    return password_context.verify(
        secret=plain_password.get_secret_value(),
        hash=hashed_password.get_secret_value(),
    )


def get_password_hash(password: SecretStr | str) -> SecretStr:
    """
    Encode a plain text password through the app's CryptoContext,
    returning the resulting hash.

    :param password: The plain text password
    :return: The secret as run through the algorithm
    """

    if not isinstance(password, SecretStr):
        password = SecretStr(password)
    return SecretStr(password_context.hash(password.get_secret_value()))
