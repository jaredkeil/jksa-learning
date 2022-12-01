from app.crud.base import CRUDBase
from app.models import Standard, StandardCreate, StandardUpdate


class CRUDStandard(CRUDBase[Standard, StandardCreate, StandardUpdate]):
    ...


standard = CRUDStandard(Standard)
