import logging
from typing import Iterable

from sqlalchemy import Table
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine

# from app.deps import get_settings

from app.core.config import Settings

settings = Settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# def singleton(func):
#     instance = None
#
#     def wrapper(*args, **kwargs):
#         nonlocal instance
#         if instance is None:
#             instance = func(*args, **kwargs)
#         return instance
#     return wrapper
#
#
# # @singleton
# def get_engine(uri: str):
#     engine = create_engine(url=uri, echo=False)
#     return engine

engine = create_engine(url=settings.SQLALCHEMY_DATABASE_URI, echo=False)


def get_local_session():
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


# def create_db_and_tables():
#     # Only use if not using Alembic migrations
#     env = settings.API_ENV
#     logger.info(f"{env=}")
#
#     if env == "TEST":
#         logger.info("Dropping tables")
#         SQLModel.metadata.drop_all(engine)
#
#     logger.info("Creating tables")
#     # log_table_info(SQLModel.metadata.sorted_tables)
#     SQLModel.metadata.create_all(engine)
#
#
# def log_table_info(tables: list[Table]):
#     for table in tables:
#         cols = table.columns if isinstance(table.columns, Iterable) else None
#         col_log = ",\n\t\t".join(repr(c) for c in cols)
#         constraints = "\n".join(repr(c.parent) for c in table.constraints)
#         logger.debug(f"{table.name.upper()}:\n\t\t{col_log}")
