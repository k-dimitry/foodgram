"""Тесты management-команды seed."""
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from recipes.models import Recipe, RecipeIngredient, Tag
from tests.factories.recipes import IngredientFactory

User = get_user_model()

SEED_INGREDIENTS = [
    ('Картофель', 'г'),
    ('Морковь', 'г'),
    ('яйца куриные', 'г'),
    ('огурцы консервированные', 'г'),
    ('Майонез', 'г'),
    ('Свекла', 'г'),
    ('Капуста белокочанная', 'г'),
    ('Лук репчатый', 'г'),
    ('мука', 'г'),
    ('дрожжи сухие', 'г'),
    ('моцарелла', 'г'),
    ('Томатная паста', 'г'),
    ('Соль', 'г'),
    ('Куриное филе', 'г'),
    ('пармезан', 'г'),
    ('Хлеб', 'г'),
    ('Молоко', 'мл'),
    ('Сахар', 'г'),
    ('Сыр маскарпоне', 'г'),
    ('печенье Савоярди', 'г'),
    ('Сливки', 'мл'),
    ('Какао-порошок', 'г'),
]

SEED_ADMIN_EMAIL = 'bestpythondev@gmail.com'
SEED_USER_EMAILS = [
    'dimitry@foodgram.dev',
    'user2@foodgram.dev',
    'user3@foodgram.dev',
]
SEED_TAG_SLUGS = ['breakfast', 'lunch', 'dinner', 'dessert']


@pytest.fixture
def seed_ingredients(db):
    """Создаёт ингредиенты, которые ищет seed-команда."""
    for name, unit in SEED_INGREDIENTS:
        IngredientFactory(name=name, measurement_unit=unit)


def _run_seed(*args):
    """Запускает seed, глушит stdout."""
    call_command('seed', *args, stdout=StringIO())


@pytest.mark.django_db
def test_seed_creates_tags_users_recipes(seed_ingredients):
    _run_seed()

    assert Tag.objects.count() == 4
    assert set(Tag.objects.values_list('slug', flat=True)) == set(SEED_TAG_SLUGS)
    assert User.objects.filter(email=SEED_ADMIN_EMAIL).count() == 1
    assert User.objects.filter(email__in=SEED_USER_EMAILS).count() == 3
    assert Recipe.objects.count() == 6


@pytest.mark.django_db
def test_seed_recipes_have_tags_and_ingredients(seed_ingredients):
    _run_seed()

    for recipe in Recipe.objects.all():
        assert recipe.tags.count() >= 1
        assert recipe.recipe_ingredients.count() >= 4


@pytest.mark.django_db
def test_seed_admin_has_admin_flags(seed_ingredients):
    _run_seed()

    admin = User.objects.get(email=SEED_ADMIN_EMAIL)
    assert admin.is_staff is True
    assert admin.is_superuser is True


@pytest.mark.django_db
def test_seed_admin_password_works(seed_ingredients):
    _run_seed()

    admin = User.objects.get(email=SEED_ADMIN_EMAIL)
    assert admin.check_password('admin12345') is True


@pytest.mark.django_db
def test_seed_is_idempotent(seed_ingredients):
    _run_seed()
    tags_before = Tag.objects.count()
    users_before = User.objects.count()
    recipes_before = Recipe.objects.count()

    _run_seed()

    assert Tag.objects.count() == tags_before
    assert User.objects.count() == users_before
    assert Recipe.objects.count() == recipes_before
    assert tags_before == 4
    assert recipes_before == 6


@pytest.mark.django_db
def test_seed_flush_recreates_data(seed_ingredients):
    _run_seed()
    first_recipe_ids = set(Recipe.objects.values_list('id', flat=True))

    _run_seed('--flush')

    assert Tag.objects.count() == 4
    assert User.objects.filter(email__in=SEED_USER_EMAILS).count() == 3
    assert Recipe.objects.count() == 6

    new_recipe_ids = set(Recipe.objects.values_list('id', flat=True))
    assert first_recipe_ids != new_recipe_ids


@pytest.mark.django_db
def test_seed_creates_recipe_ingredients(seed_ingredients):
    _run_seed()

    assert RecipeIngredient.objects.count() == 29
