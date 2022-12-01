from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app import crud
from app.deps import (
    get_session,
    get_current_active_superuser,
    get_current_user)
from app.models import (Card, CardCreate, CardUpdate, CardRead,
                        User, ResourceReadWithCards, CardReadWithResource)

router = APIRouter()


@router.post('/', status_code=201, response_model=CardReadWithResource)
def create_card(
        *,
        card_in: CardCreate,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
) -> Any:
    """
    Create a flashcard for a resource.
    """
    resource = crud.resource.get(session, card_in.resource_id)

    if not resource:
        raise HTTPException(
            404, f'Resource with ID {card_in.resource_id} not found')
    if current_user != resource.creator:
        raise HTTPException(
            401, f'Not creator of Resource with ID {resource.id}.')

    card = crud.card.create(session, obj_in=card_in)
    return card


@router.get('/{card_id}', status_code=200, response_model=CardReadWithResource)
def fetch_card(
        *,
        card_id: int,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
) -> Any:

    card = crud.card.get(session, card_id)
    if not card:
        raise HTTPException(404, f'Card with ID {card_id} not found')
    if card.resource.private and card.resource.creator != current_user:
        raise HTTPException(
            401, f'Not creator of Resource for Card {card_id}.')
    return card


@router.get('/', status_code=200, response_model=ResourceReadWithCards)
def fetch_cards_by_resource(
        *,
        resource_id: int,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
) -> Any:
    """
    Get the flashcards for a resource.
    """
    resource = crud.resource.get(session, resource_id)
    if not resource:
        raise HTTPException(
            404, f'Resource with ID {resource_id} not found')
    if resource.private and current_user != resource.creator:
        raise HTTPException(
            401, f'Not creator of Resource with ID {resource_id}.')
    print(resource)
    return resource


@router.patch('/{card_id}', status_code=200, response_model=CardReadWithResource)
def update_card(
        *,
        card_id: int,
        card_in: CardUpdate,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
) -> Any:
    """
    Update a card. Must belong to a resource created by current logged-in user.
    """
    db_card = crud.card.get(session, card_id)
    if db_card.resource.creator != current_user:
        raise HTTPException(
            401, f'Not creator of Resource for Card with ID {card_id}.')
    return crud.card.update(session, db_obj=db_card, obj_in=card_in)
