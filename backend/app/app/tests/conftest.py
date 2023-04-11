import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from pytest import FixtureRequest
from pytest_postgresql.executor_noop import NoopExecutor
from pytest_postgresql.factories import postgresql_noproc
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import Settings
from app.deps import get_session
from app.initial_data import create_first_superuser
from app.main import app
from app.tests.tools.mock_user import (
    get_superuser_token_headers,
    authentication_token_from_email,
)

settings = Settings()

postgresql_external = postgresql_noproc(
    host=settings.POSTGRES_SERVER,
    user=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    dbname=settings.POSTGRES_DB,
)


@pytest.fixture(name="test_settings", scope="session")
def settings_fixture() -> Settings:
    return settings


@pytest.fixture(scope="session")
def engine(request: FixtureRequest):
    """ Initialize a fresh testing db (for each xdist worker), yield an engine"""
    noop_exec: NoopExecutor = request.getfixturevalue("postgresql_external")
    with DatabaseJanitor(
            user=noop_exec.user,
            host=noop_exec.host,
            port=noop_exec.port,
            dbname=noop_exec.dbname,
            version=noop_exec.version,
            password=noop_exec.password,
    ):
        uri = PostgresDsn.build(
            scheme="postgresql",
            user=noop_exec.user,
            password=noop_exec.password,
            host=noop_exec.host,
            path=f"/{noop_exec.dbname}",
        )
        engine = create_engine(uri)
        db_setup(engine)
        yield engine
    engine.dispose()


def db_setup(db_engine: Engine) -> None:
    """Perform all necessary table creation.
    Could probably use Alembic as well
    """
    SQLModel.metadata.create_all(db_engine)


@pytest.fixture(name="session")
def session_fixture(engine: Engine):
    with Session(engine) as session:
        for table in reversed(SQLModel.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        create_first_superuser(settings, session)
        yield session


@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="superuser_token_headers")
def superuser_token_headers_fixture(
        client: TestClient, session: Session
) -> dict[str, str]:
    return get_superuser_token_headers(client, session, settings)


@pytest.fixture(name="normal_user_token_headers")
def normal_user_token_headers_fixture(
        client: TestClient, session: Session
) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, session=session, email=settings.EMAIL_TEST_USER
    )
