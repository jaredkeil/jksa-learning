from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app import crud, deps
from app.deps import BatchQueryParams
from app.models import StandardRead

router = APIRouter()


@router.get(
    "/{standard_id}",
    response_model=StandardRead,
    dependencies=[Depends(deps.get_current_user)],
)
def fetch_standard(
    *, standard_id: int, session: Session = Depends(deps.get_session)
) -> Any:
    """
    Fetch a standard by ID.
    """
    standard = crud.standard.get(session, standard_id)
    if not standard:
        raise HTTPException(404, f"Standard with ID {standard_id} not found")
    return standard


@router.get(
    "/",
    response_model=list[StandardRead],
    dependencies=[Depends(deps.get_current_user)],
)
def fetch_all_standards(
    *, batch: BatchQueryParams = Depends(), session: Session = Depends(deps.get_session)
) -> Any:
    """
    Fetch all standards. Must be a logged-in user.
    """
    return crud.standard.get_multi(session, skip=batch.skip, limit=batch.limit)
