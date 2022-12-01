from app.crud.base import CRUDBase
from app.models import Card, CardCreate, CardUpdate


class CRUDCard(CRUDBase[Card, CardCreate, CardUpdate]):
    ...


card = CRUDCard(Card)
