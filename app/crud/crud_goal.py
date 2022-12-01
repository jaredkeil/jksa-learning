from app.crud.base import CRUDBase
from app.models import Goal, GoalCreate, GoalUpdate


class CRUDGoal(CRUDBase[Goal, GoalCreate, GoalUpdate]):
    pass


goal = CRUDGoal(Goal)
