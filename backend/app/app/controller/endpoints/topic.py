from fastapi import APIRouter, Depends
from sqlmodel import Session

from app import crud
from app.deps import get_session, get_current_active_superuser
from app.models import TopicCreate, TopicRead

router = APIRouter()


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(get_current_active_superuser)],
    response_model=TopicRead,
)
def create_topic(*, topic_in: TopicCreate, session: Session = Depends(get_session)):
    return crud.topic.create(session, obj_in=topic_in)
