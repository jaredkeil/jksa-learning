import os
import pathlib
from typing import Optional, Any

from pydantic import AnyHttpUrl, BaseSettings, validator, EmailStr, PostgresDsn

# Project Directories
ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent.parent.parent


class Settings(BaseSettings):
    ENVIRONMENT: str = 'local' if os.getenv('ENVIRONMENT') is not None else 'dev'
    API_V1_STR: str = "/api/v1"
    JWT_SECRET: str = "TEST_SECRET_DO_NOT_USE_IN_PROD"
    ALGORITHM: str = "HS256"

    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins e.g: '[
    # "http://localhost", "http://localhost:4200", "http://localhost:3000",
    # \ "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8001",
    ]

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
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, Any]
                               ) -> Any:
        # print('assembling db connection')
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER") if os.getenv('ENVIRONMENT') else "localhost",
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PW: str
    EMAIL_TEST_USER: EmailStr = "test@example.com"

    class Config:
        # Useful for local development
        case_sensitive = True
        # env_file = "../../.env"
        env_file = PROJECT_ROOT / '.env'


settings = Settings()
