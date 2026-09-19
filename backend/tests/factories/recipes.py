"""Фабрики для моделей приложения recipes."""
import base64

import factory
from django.core.files.uploadedfile import SimpleUploadedFile

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from tests.factories.users import UserFactory

# Минимальный валидный PNG 1×1
MINI_PNG_B64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8'
    'z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
)


def _make_mini_png() -> SimpleUploadedFile:
    """Отдаёт валидный 1×1 PNG для ImageField."""
    return SimpleUploadedFile(
        name='test.png',
        content=base64.b64decode(MINI_PNG_B64),
        content_type='image/png',
    )


class TagFactory(factory.django.DjangoModelFactory):
    """Тег с уникальными name и slug."""

    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f'Тег {n}')
    slug = factory.Sequence(lambda n: f'tag-{n}')


class IngredientFactory(factory.django.DjangoModelFactory):
    """Ингредиент с уникальным name (unit='г')."""

    class Meta:
        model = Ingredient

    name = factory.Sequence(lambda n: f'Ингредиент {n}')
    measurement_unit = 'г'


class RecipeFactory(factory.django.DjangoModelFactory):
    """Рецепт с автором и картинкой. short_code генерится в save()."""

    class Meta:
        model = Recipe

    author = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'Рецепт {n}')
    image = factory.LazyFunction(_make_mini_png)
    text = factory.Faker('text', max_nb_chars=200)
    cooking_time = 10


class RecipeIngredientFactory(factory.django.DjangoModelFactory):
    """Связь recipe ↔ ingredient с amount=100."""

    class Meta:
        model = RecipeIngredient

    recipe = factory.SubFactory(RecipeFactory)
    ingredient = factory.SubFactory(IngredientFactory)
    amount = 100


class FavoriteFactory(factory.django.DjangoModelFactory):
    """Избранное: user + recipe."""

    class Meta:
        model = Favorite

    user = factory.SubFactory(UserFactory)
    recipe = factory.SubFactory(RecipeFactory)


class ShoppingCartFactory(factory.django.DjangoModelFactory):
    """Список покупок: user + recipe."""

    class Meta:
        model = ShoppingCart

    user = factory.SubFactory(UserFactory)
    recipe = factory.SubFactory(RecipeFactory)
