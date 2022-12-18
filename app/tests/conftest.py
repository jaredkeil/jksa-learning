import pytest

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.tests.tools.utils import get_superuser_token_headers, authentication_token_from_email
from app.core.config import settings
from app.main import app
from app.deps import get_session
from ..init_db import create_first_superuser

HOST = 'localhost'
PORT = '5432'
USER = 'postgres'
PW = 'password'
DB = 'app'

POSTGRESQL_URL = settings.SQLALCHEMY_DATABASE_URI
print(f'{POSTGRESQL_URL=}')

# logging.basicConfig(level='info')
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def engine():
    return create_engine(POSTGRESQL_URL)


@pytest.fixture(scope="session")
def tables(engine):
    SQLModel.metadata.drop_all(engine)  # in case final drop_all failed
    SQLModel.metadata.create_all(engine)
    create_first_superuser()
    yield
    # SQLModel.metadata.drop_all(engine)


@pytest.fixture(name='session', scope='function')
def session_fixture(engine, tables):
    with engine.connect() as connection:
        with connection.begin() as transaction:
            with Session(connection) as sess:
                yield sess
            transaction.rollback()


@pytest.fixture(name='client')
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name='superuser_token_headers')
def superuser_token_headers_fixture(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(name='normal_user_token_headers')
def normal_user_token_headers_fixture(client: TestClient, session: Session
                                      ) -> dict[str, str]:
    return authentication_token_from_email(client=client, session=session,
                                           email=settings.EMAIL_TEST_USER)
