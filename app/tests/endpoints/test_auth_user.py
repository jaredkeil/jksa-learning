from app import crud
from app.core.config import settings
from app.models import Role, UserCreate, UserRead
from app.tests.tools.mock_data import create_random_user, pprint_dict
from app.tests.tools.mock_params import random_email
from app.tests.tools.mock_user import (get_user_from_token_headers,
                                       random_password)


def test_auth_non_exist_user():
    pass


def test_create_user_minimal(client):
    response = client.post(
        'auth/signup',
        json={'email': 'create_user_minimal@example.com',
              'password': random_password()}
    )
    data = response.json()
    assert response.status_code == 201
    assert 'password' not in data
    assert 'hashed_pw' not in data
    assert data['email'] == 'create_user_minimal@example.com'
    assert isinstance(data['id'], int)
    assert data['role'] is None
    assert data['first_name'] is None
    assert data['last_name'] is None


def test_create_user_all_fields(client):
    response = client.post(
        '/auth/signup',
        json={'email': 'create_user_all_fields@example.com',
              'password': random_password(),
              'first_name': 'John',
              'last_name': 'Smith',
              'display_name': 'first_user_yay!',
              'role': 'teacher'}
    )
    data = response.json()
    assert response.status_code == 201
    assert 'password' not in data
    assert 'hashed_pw' not in data
    assert data['email'] == 'create_user_all_fields@example.com'
    assert isinstance(data['id'], int)
    assert data['role'] == Role.teacher
    assert data['first_name'] == 'John'
    assert data['last_name'] == 'Smith'
    assert data['display_name'] == 'first_user_yay!'


def test_create_user_invalid_email(client):
    response = client.post(
        '/auth/signup',
        json={'email': 'invalid.com',
              'password': random_password()}
    )
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ['body', 'email']


def test_create_user_missing_password(client):
    response = client.post(
        '/auth/signup',
        json={'email': random_email()}
    )
    pprint_dict(response.json())
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ['body', 'password']


def test_create_user_invalid_password(client):
    response = client.post(
        '/auth/signup',
        json={'email': random_email(), 'password': 'no numbers'}
    )
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ['body', 'password']


def test_create_user_duplicate(client, session):
    user = create_random_user(session)
    response = client.post(
        '/auth/signup',
        json={'email': user.email,
              'password': random_password()}
    )
    assert response.status_code == 400


def test_login(client, session):
    user_in = UserCreate(email=random_email(), password=random_password())
    user = crud.user.create(session, obj_in=user_in)
    response = client.post(
        '/auth/login',
        data={'username': user.email,
              'password': user_in.password.get_secret_value()}
    )
    data = response.json()
    assert response.status_code == 200
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'


def test_login_incorrect_password(client, session):
    user_in = UserCreate(email=random_email(), password=random_password())
    user = crud.user.create(session, obj_in=user_in)
    response = client.post(
        '/auth/login',
        data={'username': user.email,
              'password': user_in.password.get_secret_value()[::-1]}  # :p
    )
    data = response.json()
    assert response.status_code == 400
    assert 'access_token' not in data


def test_get_me_normal_user(client, normal_user_token_headers):
    response = client.get('/user/me', headers=normal_user_token_headers)
    data = response.json()
    assert response.status_code == 200
    assert data
    assert data['email'] == settings.EMAIL_TEST_USER
    assert not data["is_superuser"]
    assert data['first_name'] is None
    assert data['last_name'] is None
    assert data['display_name'] is None
    assert data['role'] is None
    assert 'hashed_password' not in data
    assert 'password' not in data


def test_get_me_invalid_headers(client):
    bad_headers = {"Authorization": "Bearer invalid_bearer_test"}
    response = client.get('/user/me', headers=bad_headers)
    assert response.status_code == 401


def test_get_all_users(client, session, superuser_token_headers):
    superuser = get_user_from_token_headers(client, superuser_token_headers)
    users = [superuser] + [create_random_user(session) for _ in range(5)]
    response = client.get('/user/', headers=superuser_token_headers)
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 200
    assert data == [UserRead.from_orm(u).dict() for u in users]


def test_get_all_users_as_non_superuser(
        client, session, normal_user_token_headers
):
    _ = [create_random_user(session) for _ in range(2)]
    response = client.get('/user/', headers=normal_user_token_headers)
    assert response.status_code == 400


def test_update_me_normal_user(client, session, normal_user_token_headers):
    og_user_db = get_user_from_token_headers(client, normal_user_token_headers)
    og_hash = og_user_db.hashed_password
    response = client.patch(
        '/user/me',
        json={'first_name': 'Mulberry', 'last_name': 'Chancellor'},
        headers=normal_user_token_headers
    )
    data = response.json()
    user_db = get_user_from_token_headers(client, normal_user_token_headers)
    assert data['email'] == settings.EMAIL_TEST_USER  # no change
    assert data['first_name'] == 'Mulberry'
    assert data['first_name'] == user_db.first_name
    assert data['last_name'] == 'Chancellor'
    assert data['last_name'] == user_db.last_name
    assert 'password' not in data
    assert 'hashed_password' not in data
    assert user_db.hashed_password == og_hash


def test_update_me_password_email_normal_user(
        client, session, normal_user_token_headers
):
    user = get_user_from_token_headers(client, normal_user_token_headers)
    og_user_db = crud.user.get(session, user.id)
    og_hash = og_user_db.hashed_password
    og_email = og_user_db.email
    og_first_name = og_user_db.first_name
    og_last_name = og_user_db.last_name
    og_is_superuser = og_user_db.is_superuser
    og_user_display_name = og_user_db.display_name
    response = client.patch(
        '/user/me',
        json={'email': 'new@ex.com', 'password': random_password()},
        headers=normal_user_token_headers
    )
    data = response.json()
    assert response.status_code == 200
    assert data['email'] == 'new@ex.com'
    assert 'password' not in data
    assert 'hashed_password' not in data
    user_db = crud.user.get(session, user.id)
    assert user_db.hashed_password != og_hash
    assert user_db.email != og_email
    assert user_db.first_name == og_first_name
    assert user_db.last_name == og_last_name
    assert user_db.is_superuser == og_is_superuser
    assert user_db.display_name == og_user_display_name


def test_update_me_invalid_password(
        client, session, normal_user_token_headers
):
    response = client.patch(
        '/user/me',
        json={'email': 'new@ex.com', 'password': 'short'},
        headers=normal_user_token_headers
    )
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ['body', 'password']


def test_update_me_normal_user_non_allowed_fields(
        client, session, normal_user_token_headers
):
    # verify body keys not actually in UserUpdate object are ignored
    response = client.patch(
        '/user/me',
        json={'email': 'new@ex.com', 'is_superuser': True},
        headers=normal_user_token_headers
    )
    data = response.json()
    pprint_dict(data)
    assert response.status_code == 200
    user = get_user_from_token_headers(client, normal_user_token_headers)
    user_db = crud.user.get(session, user.id)
    assert user_db.email == 'new@ex.com'
    assert data['email'] == 'new@ex.com'
    assert not user_db.is_superuser
    assert not data['is_superuser']
