import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import PROJECT_ROOT, Settings
from app.deps import get_session, get_settings
from app.initial_data import create_first_superuser
from app.main import app
from app.tests.tools.mock_user import (
    get_superuser_token_headers,
    authentication_token_from_email,
)


@pytest.fixture(name="test_settings", scope="session")
def settings_fixture():
    return Settings(_env_file=PROJECT_ROOT / ".env.test")


@pytest.fixture(scope="session")
def engine(test_settings: Settings) -> Engine:
    return create_engine(test_settings.SQLALCHEMY_DATABASE_URI)


@pytest.fixture(scope="session")
def tables(engine: Engine, test_settings: Settings):
    SQLModel.metadata.drop_all(engine)  # in case final drop_all failed
    SQLModel.metadata.create_all(engine)
    create_first_superuser(test_settings)
    yield
    # SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session", scope="function")
def session_fixture(engine, tables):
    with engine.connect() as connection:
        with connection.begin() as transaction:
            with Session(connection) as sess:
                yield sess
            transaction.rollback()


@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session, test_settings: Settings):
    def get_session_override():
        return session

    def get_settings_override():
        return test_settings

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_settings] = get_settings_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="superuser_token_headers")
def superuser_token_headers_fixture(
        client: TestClient, test_settings: Settings
) -> dict[str, str]:
    return get_superuser_token_headers(client, test_settings)


@pytest.fixture(name="normal_user_token_headers")
def normal_user_token_headers_fixture(
        client: TestClient, session: Session, test_settings: Settings
) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, session=session, email=test_settings.EMAIL_TEST_USER
    )
