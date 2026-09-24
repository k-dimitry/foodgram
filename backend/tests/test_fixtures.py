"""Проверка, что все клиенты и объекты работают."""

from tests.factories.users import UserFactory
from users.models import User


def test_user_fixture_creates_user(user):
    assert isinstance(user, User)
    assert user.id is not None


def test_another_user_fixture_differs_from_user(user, another_user):
    assert another_user.id != user.id


def test_admin_user_fixture_has_admin_flags(admin_user):
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True


def test_tag_fixture_creates_tag(tag):
    assert tag.id is not None
    assert tag.slug.startswith('tag-')


def test_ingredient_fixture_creates_ingredient(ingredient):
    assert ingredient.id is not None
    assert ingredient.measurement_unit == 'г'


def test_recipe_fixture_uses_user_as_author(recipe, user):
    assert recipe.id is not None
    assert recipe.author.id == user.id


def test_api_client_is_anonymous(api_client):
    response = api_client.get('/api/users/me/')

    assert response.status_code == 401


def test_auth_client_authenticated_as_user(auth_client, user):
    response = auth_client.get('/api/users/me/')

    assert response.status_code == 200
    assert response.data['id'] == user.id
    assert response.data['email'] == user.email


def test_another_user_client_authenticated_as_another_user(
    another_user_client,
    another_user,
    user,
):
    response = another_user_client.get('/api/users/me/')

    assert response.status_code == 200
    assert response.data['id'] == another_user.id
    assert response.data['id'] != user.id


def test_admin_client_authenticated_as_admin(admin_client, admin_user):
    response = admin_client.get('/api/users/me/')

    assert response.status_code == 200
    assert response.data['id'] == admin_user.id
    assert response.data['email'] == admin_user.email


def test_auth_client_factory_creates_client_for_arbitrary_user(
    auth_client_factory,
):
    custom_user = UserFactory()
    client = auth_client_factory(custom_user)

    response = client.get('/api/users/me/')

    assert response.status_code == 200
    assert response.data['id'] == custom_user.id
