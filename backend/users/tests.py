"""Тесты API приложения users."""
import pytest
from rest_framework import status
from rest_framework.authtoken.models import Token

from tests.factories.recipes import MINI_PNG_B64, RecipeFactory
from tests.factories.users import DEFAULT_PASSWORD, FollowFactory
from users.models import Follow

VALID_AVATAR_DATA_URI = f'data:image/png;base64,{MINI_PNG_B64}'


def test_login_with_valid_credentials_returns_token(api_client, user):
    response = api_client.post(
        '/api/auth/token/login/',
        {'email': user.email, 'password': DEFAULT_PASSWORD},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    token = Token.objects.get(user=user)
    assert response.data['auth_token'] == token.key


def test_login_with_wrong_password_returns_400(api_client, user):
    response = api_client.post(
        '/api/auth/token/login/',
        {'email': user.email, 'password': 'wrong_password_999'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_with_nonexistent_email_returns_400(api_client, db):
    response = api_client.post(
        '/api/auth/token/login/',
        {'email': 'nobody@example.com', 'password': 'any_password_123'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_logout_invalidates_token(auth_client, user):
    assert Token.objects.filter(user=user).count() == 1

    response = auth_client.post('/api/auth/token/logout/')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Token.objects.filter(user=user).count() == 0


def test_me_after_logout_returns_401(auth_client, user):
    auth_client.post('/api/auth/token/logout/')

    response = auth_client.get('/api/users/me/')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_register_user_returns_201_without_password(api_client, db):
    payload = {
        'email': 'new@example.com',
        'username': 'newuser',
        'first_name': 'New',
        'last_name': 'User',
        'password': 'SecurePass99',
    }

    response = api_client.post('/api/users/', payload, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['email'] == 'new@example.com'
    assert response.data['username'] == 'newuser'
    assert response.data['first_name'] == 'New'
    assert response.data['last_name'] == 'User'
    assert 'password' not in response.data


@pytest.mark.parametrize('field', ['email', 'username'])
def test_register_with_duplicate_field_returns_400(api_client, user, field):
    payload = {
        'email': 'unique@example.com',
        'username': 'unique_user',
        'first_name': 'X',
        'last_name': 'Y',
        'password': 'SecurePass99',
    }
    payload[field] = getattr(user, field)

    response = api_client.post('/api/users/', payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert field in response.data


@pytest.mark.parametrize(
    'field',
    ['email', 'username', 'first_name', 'last_name', 'password'],
)
def test_register_without_required_field_returns_400(api_client, db, field):
    payload = {
        'email': 'new@example.com',
        'username': 'newuser',
        'first_name': 'New',
        'last_name': 'User',
        'password': 'SecurePass99',
    }
    payload.pop(field)

    response = api_client.post('/api/users/', payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert field in response.data


def test_users_list_is_paginated(api_client, user, another_user):
    response = api_client.get('/api/users/')

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data.keys()) == {'count', 'next', 'previous', 'results'}
    assert response.data['count'] == 2
    assert len(response.data['results']) == 2


def test_user_detail_returns_full_data(api_client, user):
    response = api_client.get(f'/api/users/{user.id}/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == user.id
    assert response.data['email'] == user.email
    assert response.data['username'] == user.username
    assert response.data['first_name'] == user.first_name
    assert response.data['last_name'] == user.last_name
    assert response.data['is_subscribed'] is False


def test_user_detail_nonexistent_returns_404(api_client, db):
    response = api_client.get('/api/users/99999/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_me_returns_authenticated_user(auth_client, user):
    response = auth_client.get('/api/users/me/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == user.id
    assert response.data['email'] == user.email


def test_set_password_changes_password(auth_client, user):
    new_password = 'BrandNewPass456'

    response = auth_client.post(
        '/api/users/set_password/',
        {'current_password': DEFAULT_PASSWORD, 'new_password': new_password},
        format='json',
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.check_password(new_password) is True
    assert user.check_password(DEFAULT_PASSWORD) is False


def test_set_password_with_wrong_current_returns_400(auth_client, user):
    response = auth_client.post(
        '/api/users/set_password/',
        {'current_password': 'wrong_current_xx', 'new_password': 'BrandNewPass456'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    user.refresh_from_db()
    assert user.check_password(DEFAULT_PASSWORD) is True


def test_set_password_too_short_returns_400(auth_client, user):
    response = auth_client.post(
        '/api/users/set_password/',
        {'current_password': DEFAULT_PASSWORD, 'new_password': 'short'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_avatar_upload_returns_url_and_saves_file(auth_client, user):
    response = auth_client.put(
        '/api/users/me/avatar/',
        {'avatar': VALID_AVATAR_DATA_URI},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.avatar.name.startswith('users/avatars/')
    assert user.avatar.name.endswith('.png')
    assert user.avatar.name != 'users/avatars/default.png'
    assert response.data['avatar'].startswith(
        'http://testserver/media/users/avatars/',
    )


def test_avatar_upload_invalid_data_uri_returns_400(auth_client, user):
    response = auth_client.put(
        '/api/users/me/avatar/',
        {'avatar': 'not-a-data-uri'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    user.refresh_from_db()
    assert user.avatar.name == 'users/avatars/default.png'


def test_avatar_delete_resets_to_default(auth_client, user):
    auth_client.put(
        '/api/users/me/avatar/',
        {'avatar': VALID_AVATAR_DATA_URI},
        format='json',
    )

    response = auth_client.delete('/api/users/me/avatar/')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.avatar.name == 'users/avatars/default.png'


def test_avatar_delete_twice_returns_204(auth_client, user):
    auth_client.delete('/api/users/me/avatar/')

    response = auth_client.delete('/api/users/me/avatar/')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.avatar.name == 'users/avatars/default.png'


def test_subscribe_returns_201_with_user_with_recipes(
        auth_client, user, another_user,
):
    response = auth_client.post(f'/api/users/{another_user.id}/subscribe/')

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['id'] == another_user.id
    assert response.data['email'] == another_user.email
    assert response.data['is_subscribed'] is True
    assert response.data['recipes'] == []
    assert response.data['recipes_count'] == 0


def test_subscribe_self_returns_400(auth_client, user):
    response = auth_client.post(f'/api/users/{user.id}/subscribe/')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_subscribe_twice_returns_400(auth_client, user, another_user):
    auth_client.post(f'/api/users/{another_user.id}/subscribe/')

    response = auth_client.post(f'/api/users/{another_user.id}/subscribe/')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_subscribe_to_nonexistent_user_returns_404(auth_client, user):
    response = auth_client.post('/api/users/99999/subscribe/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_unsubscribe_returns_204(auth_client, user, another_user):
    FollowFactory(user=user, author=another_user)

    response = auth_client.delete(f'/api/users/{another_user.id}/subscribe/')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Follow.objects.filter(user=user, author=another_user).count() == 0


def test_unsubscribe_when_not_subscribed_returns_400(
        auth_client, user, another_user,
):
    response = auth_client.delete(f'/api/users/{another_user.id}/subscribe/')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_subscriptions_empty_returns_200_with_zero_count(auth_client, user):
    response = auth_client.get('/api/users/subscriptions/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 0
    assert response.data['results'] == []


def test_subscriptions_contains_followed_author(auth_client, user, another_user):
    FollowFactory(user=user, author=another_user)

    response = auth_client.get('/api/users/subscriptions/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == another_user.id
    assert response.data['results'][0]['is_subscribed'] is True


def test_subscriptions_recipes_limit_limits_recipes_array(
        auth_client, user, another_user,
):
    FollowFactory(user=user, author=another_user)
    RecipeFactory.create_batch(3, author=another_user)

    response = auth_client.get('/api/users/subscriptions/?recipes_limit=1')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert len(response.data['results'][0]['recipes']) == 1
    assert response.data['results'][0]['recipes_count'] == 3


PROTECTED_ENDPOINTS = [
    ('get', '/api/users/me/'),
    ('post', '/api/users/set_password/'),
    ('put', '/api/users/me/avatar/'),
    ('delete', '/api/users/me/avatar/'),
    ('post', '/api/auth/token/logout/'),
    ('get', '/api/users/subscriptions/'),
    ('post', '/api/users/1/subscribe/'),
    ('delete', '/api/users/1/subscribe/'),
]


@pytest.mark.parametrize('method,url', PROTECTED_ENDPOINTS)
def test_anonymous_receives_401_on_protected_endpoint(api_client, method, url):
    call = getattr(api_client, method)
    if method in ('post', 'put', 'patch'):
        response = call(url, {}, format='json')
    else:
        response = call(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
