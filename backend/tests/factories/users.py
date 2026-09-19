"""Фабрики для моделей приложения users."""
import factory
from django.contrib.auth import get_user_model

from users.models import Follow

User = get_user_model()

DEFAULT_PASSWORD = 'test_password_123'


class UserFactory(factory.django.DjangoModelFactory):
    """Создаёт пользователя с уникальными email/username.

    Пароль хэшируется через create_user.
    """

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = DEFAULT_PASSWORD

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', DEFAULT_PASSWORD)
        return model_class.objects.create_user(
            password=password,
            **kwargs,
        )


class FollowFactory(factory.django.DjangoModelFactory):
    """Создаёт подписку user → author (два разных пользователя)."""

    class Meta:
        model = Follow

    user = factory.SubFactory(UserFactory)
    author = factory.SubFactory(UserFactory)
