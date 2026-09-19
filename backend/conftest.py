"""Общие фикстуры и настройки для всех тестов проекта."""
import pytest
from django.contrib.auth.hashers import MD5PasswordHasher
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from tests.factories.recipes import IngredientFactory, RecipeFactory, TagFactory
from tests.factories.users import UserFactory


@pytest.fixture(autouse=True)
def _fast_password_hashing(settings):
    """MD5-хэширование паролей в тестах."""
    settings.PASSWORD_HASHERS = [
        f'{MD5PasswordHasher.__module__}.{MD5PasswordHasher.__name__}',
    ]


@pytest.fixture(autouse=True)
def _media_root_in_tmp(settings, tmp_path):
    """Медиа-файлы из тестов пишутся в tmp, не засоряют backend/media/."""
    media_root = tmp_path / 'media'
    media_root.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_ROOT = media_root


@pytest.fixture
def user(db):
    """Обычный пользователь — основной в тестах."""
    return UserFactory()


@pytest.fixture
def another_user(db):
    """Второй пользователь — для проверок «не автор»."""
    return UserFactory()


@pytest.fixture
def admin_user(db):
    """Админ (is_staff + is_superuser)."""
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def tag(db):
    """Тег."""
    return TagFactory()


@pytest.fixture
def ingredient(db):
    """Ингредиент."""
    return IngredientFactory()


@pytest.fixture
def recipe(user):
    """Рецепт, автор — user."""
    return RecipeFactory(author=user)


@pytest.fixture
def api_client():
    """Анонимный DRF-клиент."""
    return APIClient()


@pytest.fixture
def auth_client_factory(db):
    """Фабрика клиентов, авторизованных под произвольным пользователем."""

    def make(target_user):
        token, _ = Token.objects.get_or_create(user=target_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client

    return make


@pytest.fixture
def auth_client(user, auth_client_factory):
    """Клиент, авторизованный под user."""
    return auth_client_factory(user)


@pytest.fixture
def another_user_client(another_user, auth_client_factory):
    """Клиент, авторизованный под another_user."""
    return auth_client_factory(another_user)


@pytest.fixture
def admin_client(admin_user, auth_client_factory):
    """Клиент, авторизованный под admin_user."""
    return auth_client_factory(admin_user)
