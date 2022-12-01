from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, \
    Sequence

from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, SQLModel, select

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete.
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(
            self,
            session: Session,
            _id: Any
    ) -> Optional[ModelType]:
        return session.get(self.model, _id)

    def get_mult_by_ids(
            self,
            session: Session,
            ids: Sequence[int]
    ) -> list[ModelType]:
        return session.exec(
            select(self.model)
            .where(self.model.id.in_(ids))
        ).all()

    def get_multi(
            self,
            session: Session,
            *,
            skip: int = 0,
            limit: int = 5000
    ) -> List[ModelType]:
        stmt = (
            select(self.model)
            .order_by(self.model.id)
            .offset(skip)
            .limit(limit)
        )
        return session.exec(stmt).all()

    def create(
            self,
            session: Session,
            *,
            obj_in: CreateSchemaType,
            extras: Optional[dict[str, Any]] = None
    ) -> ModelType:
        db_obj = self.model.from_orm(obj_in, update=extras)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    @staticmethod
    def update(
            session: Session,
            *,
            db_obj: ModelType,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def remove(
            self,
            session: Session,
            *, _id: int
    ) -> ModelType:
        obj = session.get(self.model, _id)
        session.delete(obj)
        session.commit()
        return obj

    @staticmethod
    def refresh(session: Session, db_obj: ModelType
                ) -> ModelType:
        """Add, commit, and refresh object in Session"""
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj
