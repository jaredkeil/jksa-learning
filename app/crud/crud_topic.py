from app.crud.base import CRUDBase
from app.models import Topic


class CRUDTopic(CRUDBase[Topic, Topic, Topic]):
    ...


topic = CRUDTopic(Topic)
