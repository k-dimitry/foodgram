"""Кастомные QuerySet'ы приложения recipes."""

from django.db import models
from django.db.models import BooleanField, Exists, OuterRef, Value


class RecipeQuerySet(models.QuerySet):
    """QuerySet рецептов с флагами пользователя через подзапросы."""

    def with_user_flags(self, user) -> 'RecipeQuerySet':
        """Аннотирует is_favorited / is_in_shopping_cart для user.

        Один запрос вместо N+1. Для анонимного пользователя оба флага — False.
        """
        if user is not None and user.is_authenticated:
            from .models import Favorite, ShoppingCart

            return self.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                ),
            )
        return self.annotate(
            is_favorited=Value(False, output_field=BooleanField()),
            is_in_shopping_cart=Value(False, output_field=BooleanField()),
        )
