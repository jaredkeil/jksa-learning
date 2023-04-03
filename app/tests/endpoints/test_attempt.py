from app import crud
from app.models import Role

from app.tests.tools.mock_data import (
    create_random_user,
    create_random_laps,
    create_random_goals_with_resources,
    pprint_dict,
)
from app.tests.tools.mock_params import random_lower_string
from app.tests.tools.mock_user import authentication_token_from_email


def test_create_attempt_correct(client, session):
    goal = create_random_goals_with_resources(session)
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource)
    card = resource.cards[0]
    submission = card.answer
    student_headers = authentication_token_from_email(
        client, session, goal.student.email
    )
    response = client.post(
        "/attempt/",
        json={"lap_id": lap.id, "card_id": card.id, "submission": submission},
        headers=student_headers,
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 201
    assert data["lap"]["id"] == lap.id
    assert data["submission"] == submission
    assert data["correct"]


def test_create_attempt_incorrect(client, session):
    goal = create_random_goals_with_resources(session)
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource)
    card = resource.cards[0]
    submission = random_lower_string()
    student_headers = authentication_token_from_email(
        client, session, goal.student.email
    )
    response = client.post(
        "/attempt/",
        json={"lap_id": lap.id, "card_id": card.id, "submission": submission},
        headers=student_headers,
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 201
    assert data["lap"]["id"] == lap.id
    assert data["submission"] == submission
    assert not data["correct"]


def test_create_attempt_not_student(client, session):
    goal = create_random_goals_with_resources(session)
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource)
    card = resource.cards[0]
    submission = card.answer
    teacher_headers = authentication_token_from_email(
        client, session, goal.teacher.email
    )
    response = client.post(
        "/attempt/",
        json={"lap_id": lap.id, "card_id": card.id, "submission": submission},
        headers=teacher_headers,
    )
    data = response.json()
    assert response.status_code == 400
    assert "not a student" in data["detail"].lower()


def test_create_attempt_student_not_member(client, session):
    goal = create_random_goals_with_resources(session)
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource)
    card = resource.cards[0]
    submission = card.answer
    other_student = create_random_user(session, Role.student)
    other_student_headers = authentication_token_from_email(
        client, session, other_student.email
    )
    response = client.post(
        "/attempt/",
        json={"lap_id": lap.id, "card_id": card.id, "submission": submission},
        headers=other_student_headers,
    )
    data = response.json()
    assert response.status_code == 401
    assert "not a member" in data["detail"].lower()


def test_create_attempt_non_exist_lap(client, session):
    goal = create_random_goals_with_resources(session)
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource)
    crud.lap.remove(session, _id=lap.id)
    card = resource.cards[0]
    submission = card.answer
    student_headers = authentication_token_from_email(
        client, session, goal.student.email
    )
    response = client.post(
        "/attempt/",
        json={"lap_id": lap.id, "card_id": card.id, "submission": submission},
        headers=student_headers,
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 404
    assert "lap" in data["detail"].lower()


def test_create_attempt_non_exist_card(client, session):
    goal = create_random_goals_with_resources(session)
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource)
    card = resource.cards[0]
    crud.card.remove(session, _id=card.id)
    submission = card.answer
    student_headers = authentication_token_from_email(
        client, session, goal.student.email
    )
    response = client.post(
        "/attempt/",
        json={"lap_id": lap.id, "card_id": card.id, "submission": submission},
        headers=student_headers,
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 404
    assert "card" in data["detail"].lower()
