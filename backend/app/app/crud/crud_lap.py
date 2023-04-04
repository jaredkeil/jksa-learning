from app.crud.base import CRUDBase
from app.models import Lap, LapCreate, LapUpdate


class CRUDLap(CRUDBase[Lap, LapCreate, LapUpdate]):
    ...


lap = CRUDLap(Lap)
