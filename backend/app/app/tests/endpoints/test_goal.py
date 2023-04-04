from app import crud
from app.models import UserRead, StandardRead, ResourceReadWithCards, Role
from app.tests.tools.mock_data import (
    create_random_user,
    create_random_standards,
    create_topics,
    create_random_resources,
    create_random_goals,
    create_random_cards,
    update_user,
    create_random_groups,
    pprint_dict,
)
from app.tests.tools.mock_params import local_today
from app.tests.tools.mock_user import get_user_from_token_headers


def test_create_goal(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal_in_data = {
        "student_id": student.id,
        "standard_id": standard.id,
        "group_id": group.id,
        "start_date": "2022-07-17",
        "end_date": "2030-06-14",
        "accuracy": 100.0,
        "n_trials": 5,
    }
    response = client.post(
        "/goal/", json=goal_in_data, headers=normal_user_token_headers
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 201
    assert "id" in data
    goal = crud.goal.get(session, data["id"])
    assert data["start_date"] == goal.start_date.strftime("%Y-%m-%d")
    assert data["end_date"] == goal.end_date.strftime("%Y-%m-%d")
    assert data["accuracy"] == goal.accuracy
    assert data["n_trials"] == goal.n_trials
    assert data["teacher"] == UserRead.from_orm(teacher).dict()
    assert data["student"] == UserRead.from_orm(student).dict()
    assert data["standard"] == StandardRead.from_orm(standard).dict()
    assert data["resources"] == []


def test_create_goal_student_not_in_group(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.append(teacher)
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal_in_data = {
        "student_id": student.id,
        "standard_id": standard.id,
        "group_id": group.id,
        "end_date": "2030-06-14",
    }
    response = client.post(
        "/goal/", json=goal_in_data, headers=normal_user_token_headers
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 401
    assert "student" in data["detail"].lower()
    assert "not in" in data["detail"].lower()


def test_create_goal_teacher_not_in_group(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.append(student)
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal_in_data = {
        "student_id": student.id,
        "standard_id": standard.id,
        "group_id": group.id,
        "end_date": "2030-06-14",
    }
    response = client.post(
        "/goal/", json=goal_in_data, headers=normal_user_token_headers
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 401
    assert "teacher" in data["detail"].lower()
    assert "not in" in data["detail"].lower()


def test_create_goal_user_is_not_teacher(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    not_teacher = update_user(session, user, {"role": Role.student})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([not_teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal_in_data = {
        "student_id": student.id,
        "standard_id": standard.id,
        "group_id": group.id,
        "end_date": "2030-06-14",
    }
    response = client.post(
        "/goal/", json=goal_in_data, headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 400
    assert "teacher" in data["detail"].lower()
    assert "not" in data["detail"].lower()


def test_create_goal_student_id_is_not_student(
    client, session, normal_user_token_headers
):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    not_student = create_random_user(session, role=Role.teacher)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, not_student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal_in_data = {
        "student_id": not_student.id,
        "standard_id": standard.id,
        "group_id": group.id,
        "end_date": "2030-06-14",
    }
    response = client.post(
        "/goal/", json=goal_in_data, headers=normal_user_token_headers
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 422
    assert "not student" in data["detail"].lower()


def test_create_goal_non_exist_student(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    crud.user.remove(session, _id=student.id)
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal_in_data = {
        "student_id": student.id,
        "standard_id": standard.id,
        "group_id": group.id,
        "end_date": "2030-06-14",
    }
    response = client.post(
        "/goal/", json=goal_in_data, headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 404
    assert "student" in data["detail"].lower()
    assert "not found" in data["detail"].lower()


def test_create_goal_non_exist_standard(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    crud.standard.remove(session, _id=standard.id)

    goal_in_data = {
        "student_id": student.id,
        "standard_id": standard.id,
        "group_id": group.id,
        "end_date": "2030-06-14",
    }
    response = client.post(
        "/goal/", json=goal_in_data, headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 404
    assert "standard" in data["detail"].lower()
    assert "not found" in data["detail"].lower()


def test_create_goal_non_exist_group(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    crud.group.remove(session, _id=group.id)
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal_in_data = {
        "student_id": student.id,
        "standard_id": standard.id,
        "group_id": group.id,
        "end_date": "2030-06-14",
    }
    response = client.post(
        "/goal/", json=goal_in_data, headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 404
    assert "group" in data["detail"].lower()
    assert "not found" in data["detail"].lower()


def test_create_goal_accuracy_over_100(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal_in_data = {
        "student_id": student.id,
        "standard_id": standard.id,
        "group_id": group.id,
        "end_date": "2030-06-14",
        "accuracy": 110,
    }
    response = client.post(
        "/goal/", json=goal_in_data, headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 422
    assert data["detail"][0]["loc"] == ["body", "accuracy"]


def test_create_goal_accuracy_is_0(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal_in_data = {
        "student_id": student.id,
        "standard_id": standard.id,
        "group_id": group.id,
        "end_date": "2030-06-14",
        "accuracy": 0,
    }
    response = client.post(
        "/goal/", json=goal_in_data, headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 422
    assert data["detail"][0]["loc"] == ["body", "accuracy"]


def test_create_goal_accuracy_negative(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal_in_data = {
        "student_id": student.id,
        "standard_id": standard.id,
        "group_id": group.id,
        "end_date": "2030-06-14",
        "accuracy": -1,
    }
    response = client.post(
        "/goal/", json=goal_in_data, headers=normal_user_token_headers
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 422
    assert data["detail"][0]["loc"] == ["body", "accuracy"]


def test_create_goal_not_future_end_date(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal_in_data = {
        "student_id": student.id,
        "standard_id": standard.id,
        "group_id": group.id,
        "end_date": local_today().strftime("%Y-%m-%d"),
    }
    response = client.post(
        "/goal/", json=goal_in_data, headers=normal_user_token_headers
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 422
    assert data["detail"][0]["loc"] == ["body", "end_date"]


def test_get_goal_student(client, session, normal_user_token_headers):
    teacher = create_random_user(session, role=Role.teacher)
    user = get_user_from_token_headers(client, normal_user_token_headers)
    student = update_user(session, user, {"role": Role.student})
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    resource = create_random_resources(session, teacher, 1)
    create_random_cards(session, resource, 5)
    goal.resources.append(resource)
    response = client.get(f"/goal/{goal.id}", headers=normal_user_token_headers)
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 200
    assert data["id"] == goal.id
    assert data["start_date"] == goal.start_date.strftime("%Y-%m-%d")
    assert data["end_date"] == goal.end_date.strftime("%Y-%m-%d")
    assert data["accuracy"] == goal.accuracy
    assert data["n_trials"] == goal.n_trials
    assert data["teacher"] == UserRead.from_orm(teacher).dict()
    assert data["student"] == UserRead.from_orm(student).dict()
    assert data["standard"] == StandardRead.from_orm(standard).dict()
    assert data["resources"] == [ResourceReadWithCards.from_orm(resource).dict()]


def test_get_goal_teacher(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    resource = create_random_resources(session, teacher, 1)
    create_random_cards(session, resource, 5)
    goal.resources.append(resource)
    response = client.get(f"/goal/{goal.id}", headers=normal_user_token_headers)
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 200
    assert data["id"] == goal.id
    assert data["start_date"] == goal.start_date.strftime("%Y-%m-%d")
    assert data["end_date"] == goal.end_date.strftime("%Y-%m-%d")
    assert data["accuracy"] == goal.accuracy
    assert data["n_trials"] == goal.n_trials
    assert data["teacher"] == UserRead.from_orm(teacher).dict()
    assert data["student"] == UserRead.from_orm(student).dict()
    assert data["standard"] == StandardRead.from_orm(standard).dict()
    assert data["resources"] == [ResourceReadWithCards.from_orm(resource).dict()]


def test_get_goal_non_exist(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    resource = create_random_resources(session, teacher, 1)
    create_random_cards(session, resource, 5)
    goal.resources.append(resource)
    crud.goal.remove(session, _id=goal.id)
    response = client.get(f"/goal/{goal.id}", headers=normal_user_token_headers)
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 404


def test_get_goal_as_student_not_on_goal(client, session, normal_user_token_headers):
    teacher = create_random_user(session, role=Role.teacher)
    other_student = create_random_user(session, role=Role.student)
    user = get_user_from_token_headers(client, normal_user_token_headers)
    student = update_user(session, user, {"role": Role.student})
    group = create_random_groups(session, 1)
    group.users.extend([teacher, other_student, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, other_student, group, standard, n=1)
    resource = create_random_resources(session, teacher, 1)
    create_random_cards(session, resource, 5)
    goal.resources.append(resource)
    response = client.get(f"/goal/{goal.id}", headers=normal_user_token_headers)
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 401


def test_get_goal_as_teacher_not_on_goal(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    other_teacher = create_random_user(session, role=Role.teacher)
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, other_teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, other_teacher, student, group, standard, n=1)
    resource = create_random_resources(session, teacher, 1)
    create_random_cards(session, resource, 5)
    goal.resources.append(resource)
    response = client.get(f"/goal/{goal.id}", headers=normal_user_token_headers)
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 401


def test_add_resource(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    resource = create_random_resources(session, teacher, 1)
    create_random_cards(session, resource, 5)
    response = client.post(
        f"/goal/resource-link/",
        json={"goal_id": goal.id, "resource_id": resource.id},
        headers=normal_user_token_headers,
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 200
    assert data["resources"] == [ResourceReadWithCards.from_orm(resource).dict()]


def test_add_resource_not_goal_teacher(client, session, normal_user_token_headers):
    other_user = create_random_user(session)
    other_teacher = update_user(session, other_user, {"role": Role.teacher})
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session)
    group = create_random_groups(session, 1)
    group.users.extend([other_user, teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, other_teacher, student, group, standard, n=1)
    resource = create_random_resources(session, other_teacher, all_private=True)
    create_random_cards(session, resource, 5)
    response = client.post(
        f"/goal/resource-link/",
        json={"goal_id": goal.id, "resource_id": resource.id},
        headers=normal_user_token_headers,
    )
    data = response.json()
    assert response.status_code == 401
    assert "not teacher" in data["detail"].lower()


def test_add_private_resource_non_creator(client, session, normal_user_token_headers):
    other_user = create_random_user(session)
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    resource = create_random_resources(session, other_user, all_private=True)
    create_random_cards(session, resource, 5)
    response = client.post(
        f"/goal/resource-link/",
        json={"goal_id": goal.id, "resource_id": resource.id},
        headers=normal_user_token_headers,
    )
    data = response.json()
    assert response.status_code == 401
    assert "not creator" in data["detail"].lower()


def test_add_public_resource_non_creator(client, session, normal_user_token_headers):
    other_user = create_random_user(session)
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    resource = create_random_resources(session, other_user, all_public=True)
    create_random_cards(session, resource, 5)
    response = client.post(
        f"/goal/resource-link/",
        json={"goal_id": goal.id, "resource_id": resource.id},
        headers=normal_user_token_headers,
    )
    data = response.json()
    assert response.status_code == 200
    assert data["resources"] == [ResourceReadWithCards.from_orm(resource).dict()]


def test_add_non_exist_resource(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    resource = create_random_resources(session, teacher, all_public=True)
    goal.resources.append(resource)
    goal = crud.goal.refresh(session, goal)
    crud.resource.remove(session, _id=resource.id)
    response = client.post(
        f"/goal/resource-link/",
        json={"goal_id": goal.id, "resource_id": resource.id},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    assert "resource" in response.json()["detail"].lower()


def test_add_resource_non_exist_goal(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    crud.goal.remove(session, _id=goal.id)
    resource = create_random_resources(session, teacher, all_public=True)
    response = client.post(
        f"/goal/resource-link/",
        json={"goal_id": goal.id, "resource_id": resource.id},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    assert "goal" in response.json()["detail"].lower()


def test_add_multi_resources(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    resources = create_random_resources(session, teacher, n=5, all_public=True)
    for r in resources:
        create_random_cards(session, r, 3)
    resource_ids = [r.id for r in resources]
    response = client.post(
        "/goal/resource-link/multi/",
        json={"goal_id": goal.id, "resource_ids": resource_ids},
        headers=normal_user_token_headers,
    )
    data = response.json()
    assert data["resources"] == [
        ResourceReadWithCards.from_orm(r).dict() for r in resources
    ]


def test_add_multi_resources_non_exist_goal(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    resources = create_random_resources(session, teacher, n=5, all_public=True)
    resource_ids = [r.id for r in resources]
    crud.goal.remove(session, _id=goal.id)
    response = client.post(
        "/goal/resource-link/multi/",
        json={"goal_id": goal.id, "resource_ids": resource_ids},
        headers=normal_user_token_headers,
    )
    data = response.json()
    assert response.status_code == 404
    assert "goal" in data["detail"].lower()
    assert "not found" in data["detail"].lower()


def test_add_multi_non_exist_all_resources(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    resources = create_random_resources(session, teacher, n=5, all_public=True)
    resource_ids = [r.id for r in resources]
    for r in resources:
        crud.resource.remove(session, _id=r.id)
    response = client.post(
        "/goal/resource-link/multi/",
        json={"goal_id": goal.id, "resource_ids": resource_ids},
        headers=normal_user_token_headers,
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 404
    assert "resource" in data["detail"].lower()
    assert "not found" in data["detail"].lower()


def test_add_multi_resources_some_non_exist(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    resources = create_random_resources(session, teacher, n=5, all_public=True)
    resource_ids = [r.id for r in resources]
    for r in resources[:2]:
        crud.resource.remove(session, _id=r.id)
    response = client.post(
        "/goal/resource-link/multi/",
        json={"goal_id": goal.id, "resource_ids": resource_ids},
        headers=normal_user_token_headers,
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 200
    assert data["resources"] == [
        ResourceReadWithCards.from_orm(r).dict() for r in resources[2:]
    ]


def test_add_multi_resources_non_creator_public(
    client, session, normal_user_token_headers
):
    other_user = create_random_user(session, role=Role.teacher)
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    resources = create_random_resources(session, other_user, n=5, all_public=True)
    resource_ids = [r.id for r in resources]
    response = client.post(
        "/goal/resource-link/multi/",
        json={"goal_id": goal.id, "resource_ids": resource_ids},
        headers=normal_user_token_headers,
    )
    data = response.json()
    assert response.status_code == 200
    assert data["resources"] == [
        ResourceReadWithCards.from_orm(r).dict() for r in resources
    ]


def test_add_multi_resources_creator_mixed(client, session, normal_user_token_headers):
    """Request some resources from another creator which are private.
    They should be excluded. Also include some of your own resources
    in the request. ALL of those should be successfully linked to goal.
    """
    other_user = create_random_user(session, role=Role.teacher)
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, teacher, student, group, standard, n=1)
    others_resources = create_random_resources(session, other_user, n=20)
    assert any(not r.private for r in others_resources)
    own_resources = create_random_resources(session, teacher, n=20)
    all_resources = others_resources + own_resources
    resource_ids = [r.id for r in all_resources]
    response = client.post(
        "/goal/resource-link/multi/",
        json={"goal_id": goal.id, "resource_ids": resource_ids},
        headers=normal_user_token_headers,
    )
    data = response.json()
    assert response.status_code == 200
    exp_resources = [r for r in all_resources if r.creator == teacher or not r.private]
    assert data["resources"] == [
        ResourceReadWithCards.from_orm(r).dict() for r in exp_resources
    ]


def test_add_multi_resources_not_goal_teacher(
    client, session, normal_user_token_headers
):
    other_teacher = create_random_user(session, role=Role.teacher)
    user = get_user_from_token_headers(client, normal_user_token_headers)
    teacher = update_user(session, user, {"role": Role.teacher})
    student = create_random_user(session, role=Role.student)
    group = create_random_groups(session, 1)
    group.users.extend([other_teacher, teacher, student])
    topic = create_topics(session)
    standard = create_random_standards(session, topic, 1)
    goal = create_random_goals(session, other_teacher, student, group, standard, n=1)
    resources = create_random_resources(session, teacher, n=5, all_public=True)
    resource_ids = [r.id for r in resources]
    response = client.post(
        "/goal/resource-link/multi/",
        json={"goal_id": goal.id, "resource_ids": resource_ids},
        headers=normal_user_token_headers,
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 401
