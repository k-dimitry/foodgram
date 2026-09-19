"""Тесты кастомных permissions."""
import pytest
from rest_framework.test import APIRequestFactory

from tests.factories.users import UserFactory
from users.permissions import IsAdminOrReadOnly


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.mark.parametrize(
    'method,is_staff,expected',
    [
        ('GET', False, True),
        ('HEAD', False, True),
        ('OPTIONS', False, True),
        ('POST', False, False),
        ('PUT', False, False),
        ('PATCH', False, False),
        ('DELETE', False, False),

        ('POST', True, True),
        ('DELETE', True, True),
    ],
)
def test_is_admin_or_readonly_matrix(factory, db, method, is_staff, expected):
    request = getattr(factory, method.lower())('/')
    request.user = UserFactory(is_staff=is_staff)

    result = IsAdminOrReadOnly().has_permission(request, view=None)

    assert result is expected


def test_is_admin_or_readonly_denies_for_anonymous(factory, db):
    from django.contrib.auth.models import AnonymousUser

    request = factory.post('/')
    request.user = AnonymousUser()

    result = IsAdminOrReadOnly().has_permission(request, view=None)

    assert result is False
