from app.crud.base import CRUDBase
from app.models import StandardResource, StandardResourceCreate, StandardResourceUpdate

"""
There's really no reason for this class. It's used in tests,
but the endpoints themselves use the implicit relationship "magic" of 
sqlmodel/sqlalchemy. It's just easier that way.
"""


class CRUDStandardResource(
    CRUDBase[StandardResource, StandardResourceCreate, StandardResourceUpdate]
):
    ...


standard_resource = CRUDStandardResource(StandardResource)
