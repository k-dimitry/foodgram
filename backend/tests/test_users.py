"""Тесты моделей приложения users."""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from users.models import Follow

User = get_user_model()

AVATAR_DEFAULT = 'users/avatars/default.png'


def test_user_str_returns_username(user):
    assert str(user) == user.username


def test_user_username_field_is_email():
    assert User.USERNAME_FIELD == 'email'


def test_user_required_fields_are_username_first_last():
    assert User.REQUIRED_FIELDS == ['username', 'first_name', 'last_name']


def test_user_meta_ordering_is_by_id():
    assert User._meta.ordering == ('id',)


def test_user_avatar_field_default_is_default_png():
    avatar_field = User._meta.get_field('avatar')

    assert avatar_field.default == AVATAR_DEFAULT


def test_user_duplicate_email_raises_integrity_error(user):
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(
            email=user.email,
            username='different_username',
            password='some_password',
        )


def test_user_duplicate_username_raises_integrity_error(user):
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(
            email='different@example.com',
            username=user.username,
            password='some_password',
        )


def test_follow_str_returns_user_to_author(follow):
    expected = f'{follow.user.username} → {follow.author.username}'

    assert str(follow) == expected


def test_follow_meta_ordering_is_by_id():
    assert Follow._meta.ordering == ('id',)


def test_follow_duplicate_raises_integrity_error(follow):
    with pytest.raises(IntegrityError), transaction.atomic():
        Follow.objects.create(user=follow.user, author=follow.author)


def test_follow_self_raises_integrity_error(user):
    with pytest.raises(IntegrityError), transaction.atomic():
        Follow.objects.create(user=user, author=user)


def test_follow_deleted_on_user_cascade(follow):
    user_id = follow.user.id
    follow_id = follow.id

    follow.user.delete()

    assert User.objects.filter(id=user_id).count() == 0
    assert Follow.objects.filter(id=follow_id).count() == 0


def test_follow_deleted_on_author_cascade(follow):
    author_id = follow.author.id
    follow_id = follow.id

    follow.author.delete()

    assert User.objects.filter(id=author_id).count() == 0
    assert Follow.objects.filter(id=follow_id).count() == 0
