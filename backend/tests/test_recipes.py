"""Тесты моделей приложения recipes."""
import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from tests.factories.recipes import (
    FavoriteFactory,
    IngredientFactory,
    RecipeFactory,
    RecipeIngredientFactory,
    ShoppingCartFactory,
    TagFactory,
)


def test_tag_str_returns_name(tag):
    assert str(tag) == tag.name


def test_tag_meta_ordering_is_by_name():
    assert Tag._meta.ordering == ('name',)


@pytest.mark.parametrize('field', ['name', 'slug'])
def test_tag_duplicate_field_raises_integrity_error(tag, field):
    kwargs = {
        'name': f'{tag.name}_copy',
        'slug': f'{tag.slug}-copy',
        field: getattr(tag, field),
    }

    with pytest.raises(IntegrityError), transaction.atomic():
        TagFactory(**kwargs)


def test_ingredient_str_returns_name_and_unit(ingredient):
    expected = f'{ingredient.name} ({ingredient.measurement_unit})'

    assert str(ingredient) == expected


def test_ingredient_meta_ordering_is_by_name_then_id():
    assert Ingredient._meta.ordering == ('name', 'id')


def test_ingredient_duplicate_name_and_unit_raises_integrity_error(ingredient):
    with pytest.raises(IntegrityError), transaction.atomic():
        IngredientFactory(
            name=ingredient.name,
            measurement_unit=ingredient.measurement_unit,
        )


def test_recipe_str_returns_name(recipe):
    assert str(recipe) == recipe.name


def test_recipe_meta_ordering_is_by_pub_date_desc():
    assert Recipe._meta.ordering == ('-pub_date',)


def test_recipe_short_code_generated_on_save(recipe):
    assert recipe.short_code != ''
    assert len(recipe.short_code) == 6


def test_recipe_short_code_is_unique(recipe):
    another_recipe = RecipeFactory(author=recipe.author)

    assert another_recipe.short_code != recipe.short_code


def test_recipe_short_code_not_regenerated_on_resave(recipe):
    original_code = recipe.short_code

    recipe.name = 'Изменённое имя'
    recipe.save()
    recipe.refresh_from_db()

    assert recipe.short_code == original_code


def test_recipe_cooking_time_zero_raises_integrity_error(user):
    with pytest.raises(IntegrityError), transaction.atomic():
        RecipeFactory(author=user, cooking_time=0)


def test_recipe_deleted_on_author_cascade(recipe):
    recipe_id = recipe.id

    recipe.author.delete()

    assert Recipe.objects.filter(id=recipe_id).count() == 0


def test_recipe_ingredient_str_contains_recipe_ingredient_and_amount(
        recipe_ingredient,
):
    expected = (
        f'{recipe_ingredient.recipe.name}: '
        f'{recipe_ingredient.ingredient.name} — '
        f'{recipe_ingredient.amount}'
    )

    assert str(recipe_ingredient) == expected


def test_recipe_ingredient_meta_ordering_is_by_id():
    assert RecipeIngredient._meta.ordering == ('id',)


def test_recipe_ingredient_duplicate_raises_integrity_error(recipe_ingredient):
    with pytest.raises(IntegrityError), transaction.atomic():
        RecipeIngredientFactory(
            recipe=recipe_ingredient.recipe,
            ingredient=recipe_ingredient.ingredient,
            amount=999,
        )


def test_recipe_ingredient_amount_zero_raises_integrity_error(recipe, ingredient):
    with pytest.raises(IntegrityError), transaction.atomic():
        RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, amount=0)


def test_recipe_ingredient_deleted_on_recipe_cascade(recipe_ingredient):
    ri_id = recipe_ingredient.id

    recipe_ingredient.recipe.delete()

    assert RecipeIngredient.objects.filter(id=ri_id).count() == 0


def test_ingredient_delete_protected_when_used_in_recipe(recipe_ingredient):
    ingredient_id = recipe_ingredient.ingredient_id

    with pytest.raises(ProtectedError):
        recipe_ingredient.ingredient.delete()

    assert Ingredient.objects.filter(id=ingredient_id).count() == 1


def test_favorite_str_returns_user_to_recipe(favorite):
    expected = f'{favorite.user.username} → {favorite.recipe.name}'

    assert str(favorite) == expected


def test_favorite_meta_ordering_is_by_id():
    assert Favorite._meta.ordering == ('id',)


def test_favorite_duplicate_raises_integrity_error(favorite):
    with pytest.raises(IntegrityError), transaction.atomic():
        FavoriteFactory(user=favorite.user, recipe=favorite.recipe)


@pytest.mark.parametrize('cascade_field', ['user', 'recipe'])
def test_favorite_deleted_on_cascade(favorite, cascade_field):
    favorite_id = favorite.id

    getattr(favorite, cascade_field).delete()

    assert Favorite.objects.filter(id=favorite_id).count() == 0


def test_shopping_cart_str_returns_user_to_recipe(shopping_cart):
    expected = f'{shopping_cart.user.username} → {shopping_cart.recipe.name}'

    assert str(shopping_cart) == expected


def test_shopping_cart_meta_ordering_is_by_id():
    assert ShoppingCart._meta.ordering == ('id',)


def test_shopping_cart_duplicate_raises_integrity_error(shopping_cart):
    with pytest.raises(IntegrityError), transaction.atomic():
        ShoppingCartFactory(
            user=shopping_cart.user,
            recipe=shopping_cart.recipe,
        )


@pytest.mark.parametrize('cascade_field', ['user', 'recipe'])
def test_shopping_cart_deleted_on_cascade(shopping_cart, cascade_field):
    cart_id = shopping_cart.id

    getattr(shopping_cart, cascade_field).delete()

    assert ShoppingCart.objects.filter(id=cart_id).count() == 0
