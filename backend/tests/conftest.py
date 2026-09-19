"""Общие фикстуры и настройки для всех тестов."""
import pytest
from django.contrib.auth.hashers import MD5PasswordHasher


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
