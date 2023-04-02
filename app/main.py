import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .database import create_db_and_tables
from .controller.api import api_router
from .init_data import create_first_superuser, dummy_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title='JKSA Learning')
app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event('startup')
def on_startup():
    logger.info('on_event app on_startup')
    superuser = create_first_superuser()
    if settings.ENVIRONMENT == 'dev':
        dummy_data(superuser)


@app.get('/', status_code=200)
def root():
    return {"root": "success"}
