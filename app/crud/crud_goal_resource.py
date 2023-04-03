from typing import Optional

from sqlmodel import Session, select

from app.crud.base import CRUDBase
from app.models import GoalResource, GoalResourceCreate, GoalResourceUpdate


class CRUDGoalResource(CRUDBase[GoalResource, GoalResourceCreate, GoalResourceUpdate]):
    @staticmethod
    def get_link(
        session: Session, goal_id: int, resource_id: int
    ) -> Optional[GoalResource]:
        statement = (
            select(GoalResource)
            .where(GoalResource.goal_id == goal_id)
            .where(GoalResource.resource_id == resource_id)
        )
        return session.exec(statement).first()


goal_resource = CRUDGoalResource(GoalResource)
