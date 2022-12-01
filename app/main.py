import os

from fastapi import FastAPI

from .core.config import settings
from .database import create_db_and_tables
from .controller.api import api_router
from .init_db import create_first_superuser, dummy_data

app = FastAPI(title='JKSA Learning')
app.include_router(api_router)


@app.on_event('startup')
def on_startup():
    create_db_and_tables()  # todo: figure out alembic migrations
    superuser = create_first_superuser()
    # if settings.ENVIRONMENT == 'local':
    #     dummy_data(superuser)


@app.get('/', status_code=200)
def root():
    return {"root": "success"}
