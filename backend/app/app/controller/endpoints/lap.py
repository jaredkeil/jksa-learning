from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app import crud
from app.deps import get_session, get_current_student, get_current_user
from app.models import LapRead, LapCreate, User, LapReadWithAttempts

router = APIRouter()


@router.post("/", status_code=201, response_model=LapRead)
def create_lap(
    *,
    lap_in: LapCreate,
    current_student: User = Depends(get_current_student),
    session: Session = Depends(get_session),
) -> Any:
    """Start a lap on a given goal/resource"""
    g_id, r_id = lap_in.goal_id, lap_in.resource_id
    goal = crud.goal.get(session, g_id)
    resource = crud.resource.get(session, r_id)
    if not goal:
        raise HTTPException(404, f"Goal with ID {g_id} not found.")
    if not resource:
        raise HTTPException(404, f"Resource with ID {r_id} not found.")
    if current_student != goal.student:
        raise HTTPException(401, f"Not a member of Goal {g_id}.")
    return crud.lap.create(session, obj_in=lap_in)


@router.get("/{lap_id}", response_model=LapReadWithAttempts)
def get_lap_by_id(
    *,
    lap_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Any:
    lap = crud.lap.get(session, lap_id)
    if not lap:
        raise HTTPException(404, f"Lap with ID {lap_id} not found.")
    goal = crud.goal.get(session, lap.goal_id)
    if current_user != goal.student and current_user != goal.teacher:
        raise HTTPException(401, f"Not a member of associated Goal.")
    return lap
