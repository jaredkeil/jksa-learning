from app.crud.base import CRUDBase
from app.models import Group, GroupCreate, GroupUpdate


class CRUDGroup(CRUDBase[Group, GroupCreate, GroupUpdate]):
    pass


group = CRUDGroup(Group)
