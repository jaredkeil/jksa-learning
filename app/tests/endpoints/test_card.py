from app import crud
from app.models import ResourceRead, CardRead
from app.tests.tables import (
    create_random_user, create_random_resources, create_random_standards,
    create_topics, create_random_cards
)
from app.tests.utils import random_lower_string, get_user_from_token_headers


def test_create_card(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resources(session, user, 1)
    response = client.post(
        '/card/',
        json={'question': 'Who am I?',
              'answer': f'You are {user.email}',
              'resource_id': resource.id
              },
        headers=normal_user_token_headers
    )
    data = response.json()
    assert data['question'] == 'Who am I?'
    assert data['answer'] == f'You are {user.email}'
    assert data['resource'] == ResourceRead.from_orm(resource).dict()
    assert 'cards' not in data['resource']


def test_create_card_non_resource_creator(
        client, session, normal_user_token_headers
):
    user = create_random_user(session)
    resource = create_random_resources(session, user, 1)
    req_data = {'question': random_lower_string(),
                'answer': f'You are {user.email}',
                'resource_id': resource.id}
    response = client.post(
        '/card/',
        json=req_data,
        headers=normal_user_token_headers
    )
    assert response.status_code == 401


def test_create_card_non_exist_resource(
        client, session, normal_user_token_headers
):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resources(session, user)
    crud.resource.remove(session, _id=resource.id)
    req_data = {'question': random_lower_string(),
                'answer': random_lower_string(),
                'resource_id': resource.id}
    response = client.post(
        '/card/',
        json=req_data,
        headers=normal_user_token_headers
    )
    assert response.status_code == 404


def test_get_card_by_id(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resources(session, user)
    card = create_random_cards(session, resource, 1)
    response = client.get(
        f'/card/{card.id}',
        headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 200
    assert data['question'] == card.question
    assert data['answer'] == card.answer
    assert data['resource'] == ResourceRead.from_orm(card.resource).dict()


def test_get_card_by_id_non_exist(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resources(session, user)
    card = create_random_cards(session, resource, 1)
    crud.card.remove(session, _id=card.id)
    response = client.get(f'/card/{card.id}',
                          headers=normal_user_token_headers)
    data = response.json()
    assert response.status_code == 404


def test_get_card_by_id_not_creator(
        client, session, normal_user_token_headers
):
    user = create_random_user(session)
    resource = create_random_resources(session, user, n=1, all_private=True)
    card = create_random_cards(session, resource, 1)
    response = client.get(
        f'/card/{card.id}',
        headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 401
    assert 'not creator' in data['detail'].lower()


def test_get_card_by_id_public(client, session, normal_user_token_headers):
    user = create_random_user(session)
    resource = create_random_resources(session, user, 1, all_public=True)
    card = create_random_cards(session, resource, 1)
    response = client.get(
        f'/card/{card.id}',
        headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 200
    assert data['question'] == card.question
    assert data['answer'] == card.answer
    assert data['resource'] == ResourceRead.from_orm(card.resource).dict()


def test_get_cards_by_resource(
        client, session, normal_user_token_headers
):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resources(session, user)
    cards = create_random_cards(session, resource, 10)
    response = client.get(
        f'/card/?resource_id={resource.id}',
        headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 200
    assert data['cards'] == [CardRead.from_orm(card) for card in cards]
    assert data['name'] == resource.name
    assert data['private'] == resource.private
    assert data['format'] == resource.format
    assert data['id'] == resource.id


def test_get_cards_by_resource_non_exist(
        client, session, normal_user_token_headers
):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resources(session, user)
    cards = create_random_cards(session, resource, 10)
    crud.resource.remove(session, _id=resource.id)
    response = client.get(
        f'/card/?resource_id={resource.id}',
        headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 404


def test_get_cards_by_resource_not_creator(
        client, session, normal_user_token_headers
):
    # private resource
    user = create_random_user(session)
    resource = create_random_resources(session, user, n=1, all_private=True)
    cards = create_random_cards(session, resource, 1)
    response = client.get(
        f'/card/?resource_id={resource.id}',
        headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 401


def test_get_cards_by_resource_public(
        client, session, normal_user_token_headers
):
    user = create_random_user(session)
    resource = create_random_resources(session, user, n=1, all_public=True)
    cards = create_random_cards(session, resource, 3)
    response = client.get(
        f'/card/?resource_id={resource.id}',
        headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 200
    assert data['cards'] == [CardRead.from_orm(card).dict() for card in cards]
    assert data['name'] == resource.name
    assert not data['private']
    assert data['format'] == resource.format
    assert data['id'] == resource.id


def test_update_card(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resources(session, user, n=1)
    card = create_random_cards(session, resource, 1)
    card_up_dict = {'question': random_lower_string(),
                    'answer': random_lower_string()}
    response = client.patch(
        f'/card/{card.id}',
        json=card_up_dict,
        headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 200
    assert data['question'] == card_up_dict['question']
    assert data['answer'] == card_up_dict['answer']
    assert data['id'] == card.id


# It shouldn't matter if the card's resource is public or not. If you didn't
# create the resource, you can't edit a card.
# Will test both scenarios anyway.
def test_update_private_card_non_creator(
        client, session, normal_user_token_headers
):
    user = create_random_user(session)
    resource = create_random_resources(session, user, 1, all_private=True)
    card = create_random_cards(session, resource, 1)
    card_up_dict = {'question': random_lower_string(),
                    'answer': random_lower_string()}
    response = client.patch(
        f'/card/{card.id}',
        json=card_up_dict,
        headers=normal_user_token_headers
    )
    assert response.status_code == 401


def test_update_public_card_non_creator(
        client, session, normal_user_token_headers
):
    user = create_random_user(session)
    resource = create_random_resources(session, user, 1, all_public=True)
    card = create_random_cards(session, resource, 1)
    card_up_dict = {'question': random_lower_string(),
                    'answer': random_lower_string()}
    response = client.patch(
        f'/card/{card.id}',
        json=card_up_dict,
        headers=normal_user_token_headers
    )
    assert response.status_code == 401
