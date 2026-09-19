"""Проверки, что фабрики создают валидные объекты."""
import pytest

from recipes.models import Favorite, ShoppingCart
from tests.factories.recipes import (
    FavoriteFactory,
    IngredientFactory,
    RecipeFactory,
    RecipeIngredientFactory,
    ShoppingCartFactory,
    TagFactory,
)
from tests.factories.users import FollowFactory, UserFactory
from users.models import Follow

DEFAULT_PASSWORD = 'test_password_123'


@pytest.mark.django_db
def test_user_factory_creates_user_with_hashed_password():
    user = UserFactory()

    assert user.id is not None
    assert user.email.startswith('user')
    assert user.email.endswith('@example.com')
    assert user.check_password(DEFAULT_PASSWORD) is True


@pytest.mark.django_db
def test_user_factory_generates_unique_emails():
    user_1 = UserFactory()
    user_2 = UserFactory()

    assert user_1.email != user_2.email
    assert user_1.username != user_2.username


@pytest.mark.django_db
def test_follow_factory_creates_follow_between_two_users():
    follow = FollowFactory()

    assert follow.id is not None
    assert follow.user.id != follow.author.id
    assert Follow.objects.filter(
        user=follow.user, author=follow.author,
    ).count() == 1


@pytest.mark.django_db
def test_tag_factory_creates_tag_with_valid_slug():
    tag = TagFactory()

    assert tag.id is not None
    assert tag.name.startswith('Тег')
    assert tag.slug.startswith('tag-')


@pytest.mark.django_db
def test_ingredient_factory_creates_ingredient():
    ingredient = IngredientFactory()

    assert ingredient.id is not None
    assert ingredient.name.startswith('Ингредиент')
    assert ingredient.measurement_unit == 'г'


@pytest.mark.django_db
def test_recipe_factory_creates_recipe_with_short_code():
    recipe = RecipeFactory()

    assert recipe.id is not None
    assert recipe.author.id is not None
    assert recipe.cooking_time == 10
    assert recipe.short_code != ''
    assert len(recipe.short_code) == 6


@pytest.mark.django_db
def test_recipe_ingredient_factory_creates_through_row():
    ri = RecipeIngredientFactory()

    assert ri.id is not None
    assert ri.amount == 100
    assert ri.recipe.id is not None
    assert ri.ingredient.id is not None


@pytest.mark.django_db
def test_favorite_factory_creates_favorite():
    favorite = FavoriteFactory()

    assert favorite.id is not None
    assert favorite.user.id is not None
    assert favorite.recipe.id is not None
    assert Favorite.objects.filter(
        user=favorite.user, recipe=favorite.recipe,
    ).count() == 1


@pytest.mark.django_db
def test_shopping_cart_factory_creates_cart_entry():
    cart = ShoppingCartFactory()

    assert cart.id is not None
    assert cart.user.id is not None
    assert cart.recipe.id is not None
    assert ShoppingCart.objects.filter(
        user=cart.user, recipe=cart.recipe,
    ).count() == 1
