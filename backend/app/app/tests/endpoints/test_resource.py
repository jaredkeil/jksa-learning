from starlette import status

from app import crud

# from app.core.config import settings
from app.models import ResourceFormat, ResourceCreateInternal, UserRead
from app.tests.tools.mock_data import (
    create_random_resource,
    create_random_user,
    create_random_standards,
    create_topics,
    create_random_resources,
)
from app.tests.tools.mock_params import random_lower_string
from app.tests.tools.mock_user import get_user_from_token_headers

""" Create """


def test_create_resource_minimal(normal_user_token_headers, client, test_settings):
    response = client.post(
        "/resource/",
        headers=normal_user_token_headers,
        json={"name": "My First Resource"},
    )

    data = response.json()
    assert response.status_code == 201
    assert "id" in data
    assert data["name"] == "My First Resource"
    assert data["private"]
    assert data["format"] == ResourceFormat.flashcard
    assert data["creator"]["email"] == test_settings.EMAIL_TEST_USER


def test_create_resource_all_fields(normal_user_token_headers, client, test_settings):
    response = client.post(
        "/resource/",
        headers=normal_user_token_headers,
        json={
            "name": "A Fully flushed out resource",
            "private": "false",
            "format": "pdf",
        },
    )

    data = response.json()
    assert response.status_code == 201
    assert "id" in data
    assert data["name"] == "A Fully flushed out resource"
    assert not data["private"]
    assert data["format"] == ResourceFormat.pdf
    assert data["creator"]["email"] == test_settings.EMAIL_TEST_USER


def test_create_resource_without_token(client):
    response = client.post("/resource/", json={"name": "My First Resource"})

    data = response.json()
    assert response.status_code == 401


def test_create_resource_flashcard(normal_user_token_headers, client):
    response = client.post(
        "/resource/",
        headers=normal_user_token_headers,
        json={"name": random_lower_string(), "format": "flashcard"},
    )

    data = response.json()
    assert response.status_code == 201
    assert "id" in data
    assert data["format"] == ResourceFormat.flashcard
    assert data["private"]


def test_create_resource_pdf(normal_user_token_headers, client):
    response = client.post(
        "/resource/",
        headers=normal_user_token_headers,
        json={"name": random_lower_string(), "format": "pdf"},
    )

    data = response.json()
    assert response.status_code == 201
    assert "id" in data
    assert data["format"] == ResourceFormat.pdf
    assert data["private"]


def test_create_resource_private(normal_user_token_headers, client):
    response = client.post(
        "/resource/",
        headers=normal_user_token_headers,
        json={"name": random_lower_string(), "private": "true"},
    )

    data = response.json()
    assert response.status_code == 201
    assert "id" in data
    assert data["format"] == ResourceFormat.flashcard
    assert data["private"]


def test_create_resource_public(normal_user_token_headers, client):
    response = client.post(
        "/resource/",
        headers=normal_user_token_headers,
        json={"name": random_lower_string(), "private": "false"},
    )

    data = response.json()
    assert response.status_code == 201
    assert "id" in data
    assert data["format"] == ResourceFormat.flashcard
    assert not data["private"]


def test_create_non_valid_private(client, normal_user_token_headers):
    response = client.post(
        "/resource/",
        json={"name": random_lower_string(), "private": "bool"},
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_non_valid_format(client, normal_user_token_headers):
    response = client.post(
        "/resource/",
        json={"name": random_lower_string(), "private": "bool"},
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


""" Get """


def test_get_private_resource_as_creator(client, session, normal_user_token_headers):
    test_user = get_user_from_token_headers(client, normal_user_token_headers)
    resource_in = ResourceCreateInternal(
        name="private resource", private=True, creator_id=test_user.id
    )
    resource = crud.resource.create(session, obj_in=resource_in)

    response = client.get(f"/resource/{resource.id}", headers=normal_user_token_headers)

    data = response.json()
    assert response.status_code == 200
    assert data["id"] == resource.id
    assert data["private"]
    assert data["creator"] == UserRead.from_orm(test_user)


def test_get_private_as_not_creator(client, session, normal_user_token_headers):
    user_not_me = create_random_user(session)
    resource_in = ResourceCreateInternal(
        name="other user's resource", private=True, creator_id=user_not_me.id
    )
    resource_not_mine = crud.resource.create(session, obj_in=resource_in)

    response = client.get(
        f"/resource/{resource_not_mine.id}", headers=normal_user_token_headers
    )

    assert response.status_code == 401


def test_get_public_resource_as_creator(client, session, normal_user_token_headers):
    test_user = get_user_from_token_headers(client, normal_user_token_headers)
    resource_in = ResourceCreateInternal(
        name="my resource", private=False, creator_id=test_user.id
    )
    resource_public = crud.resource.create(session, obj_in=resource_in)

    response = client.get(
        f"/resource/{resource_public.id}", headers=normal_user_token_headers
    )

    data = response.json()
    assert response.status_code == 200
    assert data["name"] == "my resource"
    assert not data["private"]
    # even though it's public, since we created it, we can see our data
    assert data["creator"] == UserRead.from_orm(test_user)


def test_get_public_resource_as_not_creator(client, session, normal_user_token_headers):
    user_not_me = create_random_user(session)
    resource_in = ResourceCreateInternal(
        name="other user's resource", private=False, creator_id=user_not_me.id
    )
    resource_public = crud.resource.create(session, obj_in=resource_in)

    response = client.get(
        f"/resource/{resource_public.id}", headers=normal_user_token_headers
    )
    data = response.json()
    print(data)
    assert response.status_code == 200
    assert data["name"] == "other user's resource"
    assert not data["private"]
    assert "creator_id" not in data
    assert data["creator"] is None


def test_get_resource_does_not_exist(client, normal_user_token_headers):
    response = client.get(f"/resource/1", headers=normal_user_token_headers)
    assert response.status_code == 404


def test_get_resources(client, session, normal_user_token_headers):
    n = 20
    test_user = get_user_from_token_headers(client, normal_user_token_headers)
    resources = create_random_resources(session, test_user, n)

    response = client.get("/resource/", headers=normal_user_token_headers)
    data = response.json()  # list of dicts
    response.json()
    assert len(data) == len(resources)
    assert data == [rsc.dict(exclude={"creator_id"}) for rsc in resources]


def test_get_resources_standard(client, session, normal_user_token_headers):
    # include_public is False by default
    user1 = get_user_from_token_headers(client, normal_user_token_headers)
    user2 = create_random_user(session)
    resources1 = create_random_resources(session, user1, 10)
    resources2 = create_random_resources(session, user2, 10)
    topic = create_topics(session, 1)
    standard = create_random_standards(session, topic, 1)
    standard.resources.extend(resources1)
    standard.resources.extend(resources2)
    response = client.get(
        f"/resource/?standard_id={standard.id}", headers=normal_user_token_headers
    )
    data = response.json()  # list of dicts
    assert response.status_code == 200
    assert len(data) == len(resources1)
    assert data == [rsc.dict(exclude={"creator_id"}) for rsc in resources1]


def test_get_resources_include_public_no_standard(
    client, session, normal_user_token_headers
):
    user1 = get_user_from_token_headers(client, normal_user_token_headers)
    user2 = create_random_user(session)
    resources1 = create_random_resources(session, user1, 10)
    resources2 = create_random_resources(session, user2, 10)
    topic = create_topics(session, 1)
    standard = create_random_standards(session, topic, 1)
    standard.resources.extend(resources1 + resources2)
    response = client.get(
        "/resource/?include_public=true", headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data) == len(resources1)
    assert data == [rsc.dict(exclude={"creator_id"}) for rsc in resources1]


def test_get_resources_standard_include_public(
    client, session, normal_user_token_headers
):
    user1 = get_user_from_token_headers(client, normal_user_token_headers)
    user2 = create_random_user(session)
    resources1 = create_random_resources(session, user1, 5)
    resources2 = create_random_resources(session, user2, 20)
    topic = create_topics(session, 1)
    standard = create_random_standards(session, topic, 1)
    standard.resources.extend(resources1 + resources2)
    response = client.get(
        f"/resource/?standard_id={standard.id}&include_public=true",
        headers=normal_user_token_headers,
    )
    data = response.json()
    assert response.status_code == 200
    exp_resources = resources1 + [rsc for rsc in resources2 if not rsc.private]
    assert len(data) == len(exp_resources)
    assert data == [rsc.dict(exclude={"creator_id"}) for rsc in exp_resources]


def test_get_resources_standard_non_exist(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resources = create_random_resources(session, user, 3)
    topic = create_topics(session, 1)
    standard = create_random_standards(session, topic, 1)
    standard.resources.extend(resources)
    crud.standard.remove(session, _id=standard.id)
    response = client.get(
        f"/resource/?standard_id={standard.id}", headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 404
    assert "standard" in data["detail"].lower()


""" Link """


def test_add_standard_link(client, session, normal_user_token_headers):
    topic = create_topics(session, 1)
    standard = create_random_standards(session, topic, 1)
    print("\n", standard)
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resource(session, user)
    response = client.post(
        "/resource/standard-link/",
        json={"standard_id": standard.id, "resource_id": resource.id},
        headers=normal_user_token_headers,
    )
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == resource.name
    assert data["private"] == resource.private
    assert data["format"] == resource.format
    assert len(data["standards"]) == 1
    ret_standard = data["standards"][0]
    assert ret_standard["template"] == standard.template
    assert ret_standard["grade"] == standard.grade
    assert ret_standard["subject"] == standard.subject
    assert ret_standard["topic"]["id"] == standard.topic.id
    assert ret_standard["topic"]["description"] == standard.topic.description


def test_add_standard_link_non_exist_resource(
    client, session, normal_user_token_headers
):
    topic = create_topics(session, 1)
    standard = create_random_standards(session, topic, 1)
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resource(session, user)
    standard.resources.append(resource)
    assert resource.standards == [standard]
    crud.resource.remove(session, _id=resource.id)
    response = client.post(
        "/resource/standard-link/",
        json={"standard_id": standard.id, "resource_id": resource.id},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    assert "resource" in response.json()["detail"].lower()


def test_add_standard_link_non_exist_standard(
    client, session, normal_user_token_headers
):
    topic = create_topics(session, 1)
    standard = create_random_standards(session, topic, 1)
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resource(session, user)
    resource.standards.append(standard)
    assert standard.resources == [resource]
    crud.standard.remove(session, _id=standard.id)
    response = client.post(
        "/resource/standard-link/",
        json={"standard_id": standard.id, "resource_id": resource.id},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    assert "standard" in response.json()["detail"].lower()


def test_add_standard_link_not_creator(client, session, normal_user_token_headers):
    topic = create_topics(session, 1)
    standard = create_random_standards(session, topic, 1)
    user_not_me = create_random_user(session)
    resource = create_random_resource(session, user_not_me)
    response = client.post(
        "/resource/standard-link/",
        json={"standard_id": standard.id, "resource_id": resource.id},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 401


def test_add_standard_link_non_auth(client, session, normal_user_token_headers):
    topic = create_topics(session, 1)
    standard = create_random_standards(session, topic, 1)
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resource(session, user)
    response = client.post(
        "/resource/standard-link/",
        json={"standard_id": standard.id, "resource_id": resource.id},
    )
    assert response.status_code == 401


"""
Link Multi
"""


def test_add_multi_standard_link(client, session, normal_user_token_headers):
    topic = create_topics(session, 1)
    standards = create_random_standards(session, topic, 5)
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resource(session, user)
    standard_ids = [s.id for s in standards]
    response = client.post(
        "/resource/standard-link/multi",
        json={"resource_id": resource.id, "standard_ids": standard_ids},
        headers=normal_user_token_headers,
    )
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == resource.name
    assert data["private"] == resource.private
    assert data["format"] == resource.format
    ret_standards = data["standards"]
    assert len(ret_standards) == 5
    for ret_std, std in zip(ret_standards, standards):
        assert ret_std["template"] == std.template
        assert ret_std["grade"] == std.grade
        assert ret_std["subject"] == std.subject
        assert ret_std["topic"]["id"] == std.topic.id
        assert ret_std["topic"]["description"] == std.topic.description

    assert resource.standards == standards  # check db update


def test_add_multi_standard_link_non_exist_resource(
    client, session, normal_user_token_headers
):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resource(session, user)
    crud.resource.remove(session, _id=resource.id)
    topic = create_topics(session, 1)
    standards = create_random_standards(session, topic, 5)
    standard_ids = [s.id for s in standards]
    response = client.post(
        "/resource/standard-link/multi",
        json={"resource_id": resource.id, "standard_ids": standard_ids},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    assert "resource" in response.json()["detail"].lower()


def test_add_multi_standard_link_non_exist_standard(
    client, session, normal_user_token_headers
):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resource(session, user)
    topic = create_topics(session, 1)
    standards = create_random_standards(session, topic, 5)
    crud.standard.remove(session, _id=standards[3].id)
    crud.standard.remove(session, _id=standards[4].id)
    standard_ids = [s.id for s in standards]
    response = client.post(
        "/resource/standard-link/multi",
        json={"resource_id": resource.id, "standard_ids": standard_ids},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    assert "standard" in response.json()["detail"].lower()


def test_add_multi_standard_link_non_exist_zero_standards(
    client, session, normal_user_token_headers
):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resource(session, user)
    topic = create_topics(session, 1)
    standards = create_random_standards(session, topic, 2)
    crud.standard.remove(session, _id=standards[0].id)
    crud.standard.remove(session, _id=standards[1].id)
    standard_ids = [s.id for s in standards]
    response = client.post(
        "/resource/standard-link/multi",
        json={"resource_id": resource.id, "standard_ids": standard_ids},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    assert "standard" in response.json()["detail"].lower()


def test_add_multi_standard_link_not_creator(
    client, session, normal_user_token_headers
):
    user_not_me = create_random_user(session)
    resource = create_random_resource(session, user_not_me)
    topic = create_topics(session, 1)
    standards = create_random_standards(session, topic, 2)
    standard_ids = [s.id for s in standards]
    response = client.post(
        "/resource/standard-link/multi",
        json={"resource_id": resource.id, "standard_ids": standard_ids},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 401


def test_add_multi_standard_link_ignore_non_exist_stds(
    client, session, normal_user_token_headers
):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource = create_random_resource(session, user)
    topic = create_topics(session, 1)
    standards = create_random_standards(session, topic, 5)
    crud.standard.remove(session, _id=standards[0].id)
    crud.standard.remove(session, _id=standards[1].id)
    standard_ids = [s.id for s in standards]
    print(standard_ids)
    response = client.post(
        "/resource/standard-link/multi?ignore_non_exist_stds=true",
        json={"resource_id": resource.id, "standard_ids": standard_ids},
        headers=normal_user_token_headers,
    )
    data = response.json()
    print(data)
    assert response.status_code == 200
    assert data["name"] == resource.name
    assert data["private"] == resource.private
    assert data["format"] == resource.format
    ret_standards = data["standards"]
    for s in ret_standards:
        print(s)
    assert len(ret_standards) == 3
    for ret_std, std in zip(ret_standards, standards[2:]):
        assert ret_std["template"] == std.template
        assert ret_std["grade"] == std.grade
        assert ret_std["subject"] == std.subject
        assert ret_std["topic"]["id"] == std.topic.id
        assert ret_std["topic"]["description"] == std.topic.description

    assert resource.standards == standards[2:]  # check db update


""" Updates """


def test_resource_update(client, session, normal_user_token_headers):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    resource_in = ResourceCreateInternal(
        name=random_lower_string(),
        private=True,
        format=ResourceFormat.pdf,  # type: ignore
        creator_id=user.id,
    )
    resource = crud.resource.create(session, obj_in=resource_in)
    data_up = {
        "name": random_lower_string(),
        "private": False,
        "format": ResourceFormat.flashcard,
    }
    response = client.patch(
        f"/resource/{resource.id}", json=data_up, headers=normal_user_token_headers
    )
    data = response.json()
    print(data)
    assert response.status_code == 200
    assert data["name"] == data_up["name"]
    assert data["private"] == data_up["private"]
    assert data["format"] == data_up["format"]


def test_resource_update_not_creator(client, session, normal_user_token_headers):
    user = create_random_user(session)
    resource_in = ResourceCreateInternal(
        name=random_lower_string(),
        private=True,
        format=ResourceFormat.pdf,  # type: ignore
        creator_id=user.id,
    )
    resource = crud.resource.create(session, obj_in=resource_in)
    data_up = {
        "name": random_lower_string(),
        "private": False,
        "format": ResourceFormat.flashcard,
    }
    response = client.patch(
        f"/resource/{resource.id}", json=data_up, headers=normal_user_token_headers
    )
    assert response.status_code == 401
