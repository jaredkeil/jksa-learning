from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app import crud
from app.deps import get_session, get_current_student, get_current_user
from app.models import Attempt, AttemptCreateExternal, AttemptRead, User, \
    AttemptReadWithLap, AttemptCreateInternal

router = APIRouter()


def is_correct(submission: str, answer: str) -> bool:
    """
    Return if submission is correct. Hopefully function can be updated
    with more advanced validating methods.
    """
    def clean(string: str) -> str:
        string = string.strip().lower()
        return ' '.join(string.split())
    return clean(submission) == clean(answer)


@router.post('/', status_code=201, response_model=AttemptReadWithLap)
def create_attempt(
        *,
        attempt_in: AttemptCreateExternal,
        current_student: User = Depends(get_current_student),
        session: Session = Depends(get_session)
) -> Any:
    lap_id, card_id = attempt_in.lap_id, attempt_in.card_id
    lap = crud.lap.get(session, lap_id)
    card = crud.card.get(session, card_id)
    if not lap:
        raise HTTPException(404, f'Lap with ID {lap_id} not found.')
    if not card:
        raise HTTPException(404, f'Card with ID {card_id} not found.')
    if current_student != lap.goal.student:
        raise HTTPException(401, f'Not a member of Goal {lap.goal_id}')

    attempt_in = AttemptCreateInternal.from_orm(attempt_in)
    attempt_in.correct = is_correct(attempt_in.submission, card.answer)
    return crud.attempt.create(session, obj_in=attempt_in)


