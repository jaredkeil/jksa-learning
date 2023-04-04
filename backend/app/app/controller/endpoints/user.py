from fastapi import APIRouter, Depends
from sqlmodel import Session

from app import deps, crud
from app.models import User, UserRead, UserUpdate

router = APIRouter()


@router.get(
    "/",
    response_model=list[UserRead],
    dependencies=[Depends(deps.get_current_active_superuser)],
)
def fetch_all_user(
    skip: int = 0, limit: int = 100, session: Session = Depends(deps.get_session)
) -> list[UserRead]:
    """
    Retrieve all users. Must have superuser auth.
    """
    return crud.user.get_multi(session, skip=skip, limit=limit)


@router.get("/me", response_model=UserRead)
def fetch_user_me(current_user: User = Depends(deps.get_current_user)) -> User:
    """
    Fetch the current logged-in user.
    """
    return current_user


@router.patch("/me", response_model=UserRead)
def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(deps.get_session),
) -> User:
    """
    Update the current logged-in user.
    """
    merge_kwargs = dict(current_user.dict(), **user_in.dict(exclude_none=True))
    user_in_merge = UserUpdate(**merge_kwargs)
    return crud.user.update(session, db_obj=current_user, obj_in=user_in_merge)
