from typing import Optional

from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from app.models import GoalResource, GoalResourceCreate, GoalResourceUpdate
from app.crud.base import CRUDBase

# SelectOfScalar.inherit_cache = True


class CRUDGoalResource(CRUDBase[GoalResource,
                                GoalResourceCreate,
                                GoalResourceUpdate]):
    def get_link(
            self,
            session: Session,
            goal_id: int,
            resource_id: int
    ) -> Optional[GoalResource]:
        statement = (select(GoalResource)
                     .where(GoalResource.goal_id == goal_id)
                     .where(GoalResource.resource_id == resource_id)
                     )
        return session.exec(statement).first()


goal_resource = CRUDGoalResource(GoalResource)
