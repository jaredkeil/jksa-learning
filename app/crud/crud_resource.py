from sqlmodel import Session, select, or_, and_, not_
from sqlmodel.sql.expression import Select, SelectOfScalar

from app.crud.base import CRUDBase
from app.models import (Resource, ResourceCreateInternal, ResourceUpdate, Standard,
                        StandardResource)


SelectOfScalar.inherit_cache = True
# Select.inherit_cache = True


class CRUDResource(CRUDBase[Resource, ResourceCreateInternal, ResourceUpdate]):

    @staticmethod
    def get_multi_by_standard(session: Session, user_id: int, standard_id: int,
                              include_public: bool = False, skip: int = 0,
                              limit: int = 5000) -> list[Resource]:
        """
        Always include where creator is user.
        Only include non-private if include_public is True
        """
        stmt = (
            select(Resource)
            .join(StandardResource)
            .where(StandardResource.standard_id == standard_id)
            .where(
                or_(
                    Resource.creator_id == user_id,
                    and_(include_public, not_(Resource.private))
                )
            )
            .order_by(Resource.id)
            .offset(skip)
            .limit(limit)
        )
        return session.exec(stmt).all()


resource = CRUDResource(Resource)
