from typing import Optional, Any

from sqlmodel import Session, select

from app.core.security import get_password_hash
from app.crud.base import CRUDBase
from app.models import User, UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, session: Session, *, email: str) -> Optional[User]:
        return session.exec(select(self.model).where(self.model.email == email)).first()

    def create(
        self,
        session: Session,
        *,
        obj_in: UserCreate,
        extras: Optional[dict[str, Any]] = None
    ) -> User:
        db_obj = self.model.from_orm(obj_in, update=extras)
        db_obj.hashed_password = get_password_hash(obj_in.password)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def update(self, session: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(session, db_obj=db_obj, obj_in=update_data)

    def make_superuser(self, session: Session, *, db_obj: User) -> User:
        db_obj.is_superuser = True
        self.refresh(session, db_obj)
        return db_obj


user = CRUDUser(User)
