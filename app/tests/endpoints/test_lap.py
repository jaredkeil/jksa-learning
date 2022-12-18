from app import crud
from app.models import Role

from app.tests.tools.mock_data import (create_random_user, create_random_laps,
                                       create_random_goals_with_resources,
                                       create_random_attempts, pprint_dict)
from app.tests.tools.mock_user import authentication_token_from_email


def test_create_lap(client, session):
    goal = create_random_goals_with_resources(session, n_rsc_per=1,
                                              n_cards_per=3)
    student_headers = authentication_token_from_email(client, session,
                                                      goal.student.email)
    resource = goal.resources[0]
    response = client.post(
        '/lap/',
        json={'goal_id': goal.id, 'resource_id': resource.id},
        headers=student_headers
    )
    data = response.json()
    assert response.status_code == 201
    assert data['resource']
    assert data['goal']
    assert data['start_ts']
    assert data['score'] is None
    assert data['end_ts'] is None
    assert 'attempts' not in data


def test_create_laps_all_goal_resources(client, session):
    goal = create_random_goals_with_resources(session, n_rsc_per=3)
    student_headers = authentication_token_from_email(client, session,
                                                      goal.student.email)
    for resource in goal.resources:
        response = client.post(
            '/lap/',
            json={'goal_id': goal.id, 'resource_id': resource.id},
            headers=student_headers
        )
        data = response.json()
        # pprint_dict(data)
        assert response.status_code == 201
        assert data['id']
        assert data['resource']
        assert data['goal']
        assert data['start_ts']
        assert data['score'] is None
        assert data['end_ts'] is None

        goal_resource = crud.goal_resource.get_link(session, goal_id=goal.id,
                                                    resource_id=resource.id)
        assert len(goal_resource.laps) == 1
    assert len(crud.lap.get_multi(session)) == 3


def test_create_multiple_laps_same_resource(client, session):
    goal = create_random_goals_with_resources(session, n_rsc_per=1)
    student_headers = authentication_token_from_email(client, session,
                                                      goal.student.email)
    resource = goal.resources[0]
    datas = []
    for _ in range(3):
        response = client.post(
            '/lap/',
            json={'goal_id': goal.id, 'resource_id': resource.id},
            headers=student_headers
        )
        assert response.status_code == 201
        datas.append(response.json())
    assert len(crud.lap.get_multi(session)) == 3
    goal_resource = crud.goal_resource.get_link(session, goal_id=goal.id,
                                                resource_id=resource.id)
    assert len(goal_resource.laps) == 3


def test_create_lap_non_student(client, session):
    goal = create_random_goals_with_resources(session, n_rsc_per=1)
    teacher_headers = authentication_token_from_email(client, session,
                                                      goal.teacher.email)
    resource = goal.resources[0]
    response = client.post(
        '/lap/',
        json={'goal_id': goal.id, 'resource_id': resource.id},
        headers=teacher_headers
    )
    assert response.status_code == 400
    assert 'not a student' in response.json()['detail']


def test_create_lap_student_not_member(client, session):
    goal = create_random_goals_with_resources(session, n_rsc_per=1)
    other_student = create_random_user(session, Role.student)
    group = goal.teacher.groups[0]
    group.users.append(other_student)
    other_student_headers = authentication_token_from_email(
        client, session, other_student.email)
    resource = goal.resources[0]
    response = client.post(
        '/lap/',
        json={'goal_id': goal.id, 'resource_id': resource.id},
        headers=other_student_headers
    )
    assert response.status_code == 401
    assert 'not a member' in response.json()['detail'].lower()


def test_create_lap_non_exist_goal(client, session):
    goal = create_random_goals_with_resources(session, n_rsc_per=1,
                                              n_cards_per=3)
    student_headers = authentication_token_from_email(client, session,
                                                      goal.student.email)
    resource = goal.resources[0]
    crud.goal.remove(session, _id=goal.id)
    response = client.post(
        '/lap/',
        json={'goal_id': goal.id, 'resource_id': resource.id},
        headers=student_headers
    )
    assert response.status_code == 404
    assert 'goal' in response.json()['detail'].lower()


def test_create_lap_non_exist_resource(client, session):
    goal = create_random_goals_with_resources(session, n_rsc_per=1,
                                              n_cards_per=3)
    student_headers = authentication_token_from_email(client, session,
                                                      goal.student.email)
    resource = goal.resources[0]
    crud.resource.remove(session, _id=resource.id)
    response = client.post(
        '/lap/',
        json={'goal_id': goal.id, 'resource_id': resource.id},
        headers=student_headers
    )
    assert response.status_code == 404
    assert 'resource' in response.json()['detail'].lower()


def test_get_lap_as_teacher(client, session):
    goal = create_random_goals_with_resources(session)
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource)
    create_random_attempts(session, lap)
    headers = authentication_token_from_email(client, session,
                                              goal.teacher.email)
    response = client.get(f'lap/{lap.id}', headers=headers)
    data = response.json()
    # pprint_dict(data)
    assert response.status_code == 200
    assert data['id'] == lap.id
    assert data['start_ts']
    assert data['goal']['id'] == goal.id
    assert data['resource']['id'] == resource.id
    assert len(data['attempts']) == len(resource.cards)


def test_get_lap_as_student(client, session):
    goal = create_random_goals_with_resources(session)
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource)
    create_random_attempts(session, lap)
    headers = authentication_token_from_email(client, session,
                                              goal.student.email)
    response = client.get(f'lap/{lap.id}', headers=headers)
    data = response.json()
    # pprint_dict(data)
    assert response.status_code == 200
    assert data['id'] == lap.id
    assert data['start_ts']
    assert data['goal']['id'] == goal.id
    assert data['resource']['id'] == resource.id
    assert len(data['attempts']) == len(resource.cards)


def test_get_lap_no_attempts(client, session):
    goal = create_random_goals_with_resources(session)
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource)
    headers = authentication_token_from_email(client, session,
                                              goal.student.email)
    response = client.get(f'lap/{lap.id}', headers=headers)
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 200
    assert data['id'] == lap.id
    assert data['start_ts']
    assert data['goal']['id'] == goal.id
    assert data['resource']['id'] == resource.id
    assert len(data['attempts']) == 0


def test_get_lap_non_exist_lap(client, session):
    goal = create_random_goals_with_resources(session)
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource)
    crud.lap.remove(session, _id=lap.id)
    headers = authentication_token_from_email(client, session,
                                              goal.teacher.email)
    response = client.get(f'lap/{lap.id}', headers=headers)
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 404
    assert 'lap' in data['detail'].lower()


def test_get_lap_non_member_teacher(client, session):
    goal = create_random_goals_with_resources(session)
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource)
    other_teacher = create_random_user(session, Role.teacher)
    headers = authentication_token_from_email(client, session,
                                              other_teacher.email)
    response = client.get(f'lap/{lap.id}', headers=headers)
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 401
    assert 'not a member' in data['detail'].lower()


def test_get_lap_non_member_student(client, session):
    goal = create_random_goals_with_resources(session)
    resource = goal.resources[0]
    lap = create_random_laps(session, goal, resource)
    other_student = create_random_user(session, Role.student)
    headers = authentication_token_from_email(client, session,
                                              other_student.email)
    response = client.get(f'lap/{lap.id}', headers=headers)
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 401
    assert 'not a member' in data['detail'].lower()
