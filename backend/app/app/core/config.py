import os
import pathlib
from typing import Optional, Any

from pydantic import (
    AnyHttpUrl,
    BaseSettings,
    validator,
    EmailStr,
    PostgresDsn,
    SecretStr,
)

# Project Directories
ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent.parent.parent


class Settings(BaseSettings):
    # ENVIRONMENT: str = "local" if os.getenv("ENVIRONMENT") is not None else "dev"

    ####################
    # ALL ENVIRONMENTS #
    ####################
    API_V1_STR: str = "/api/v1"
    JWT_SECRET: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    ########################
    # ENVIRONMENT SPECIFIC #
    ########################
    API_ENV: str

    @validator("API_ENV", pre=True)
    def assemble_api_env(cls, v: str) -> str:
        if v.upper() not in ("DEV", "TEST", "STAGING", "PROD"):
            raise ValueError(v)
        return v.upper()

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins e.g: '[
    # "http://localhost", "http://localhost:4200", "http://localhost:3000",
    # \ "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    # BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = [
    #     "http://localhost:3000",
    #     "http://localhost:8001",
    # ]
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl]

    # Origins that match this regex OR are in the above list are allowed
    # BACKEND_CORS_ORIGIN_REGEX: Optional[str] = "https.*\.(netlify.app|herokuapp.com)"  # noqa: W605

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, Any]) -> Any:
        # print('assembling db connection')
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    FIRST_SUPERUSER: EmailStr = ""
    FIRST_SUPERUSER_PW: SecretStr = ""
    EMAIL_TEST_USER: EmailStr = "test@example.com"

    # class Config:
    #     # Useful for local development
    #     case_sensitive = True
    #     # env_file = "../../.env"
    #     env_file = PROJECT_ROOT / ".env"


# settings = Settings()
