from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from .constants import (
    EMAIL_MAX_LENGTH,
    FIRST_NAME_MAX_LENGTH,
    LAST_NAME_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
)


class User(AbstractUser):
    """Кастомная модель пользователя."""

    email = models.EmailField(
        'email',
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
    )
    username = models.CharField(
        'username',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator()],
    )
    first_name = models.CharField(
        'first_name',
        max_length=FIRST_NAME_MAX_LENGTH,
    )
    last_name = models.CharField(
        'last_name',
        max_length=LAST_NAME_MAX_LENGTH,
    )
    avatar = models.ImageField(
        'avatar',
        upload_to='users/avatars/',
        null=True,
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self) -> str:
        return self.username


class Follow(models.Model):
    """Подписка: user подписан на author."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user__username', 'author__username')
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_follow',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_follow',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user.username} → {self.author.username}'
