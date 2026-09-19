"""Общие фикстуры и настройки для всех тестов."""
import pytest
from django.contrib.auth.hashers import MD5PasswordHasher


@pytest.fixture(autouse=True)
def _fast_password_hashing(settings):
    """MD5-хэширование паролей в тестах."""
    settings.PASSWORD_HASHERS = [
        f'{MD5PasswordHasher.__module__}.{MD5PasswordHasher.__name__}',
    ]
