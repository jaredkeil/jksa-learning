from app.crud.base import CRUDBase
from app.models import Attempt, AttemptCreateInternal, AttemptUpdate


class CRUDAttempt(CRUDBase[Attempt, AttemptCreateInternal, AttemptUpdate]):
    ...


attempt = CRUDAttempt(Attempt)
