"""Тесты API приложения recipes."""
import pytest
from rest_framework import status

from recipes.models import Favorite, Recipe, ShoppingCart
from tests.factories.recipes import (
    IngredientFactory,
    RecipeFactory,
    TagFactory,
)
from tests.factories.users import FollowFactory

MINI_PNG_DATA_URI = (
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ'
    'AAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
)


def _recipe_create_payload(tag, ingredient, **overrides):
    """Собирает валидный payload для POST /api/recipes/."""
    payload = {
        'ingredients': [{'id': ingredient.id, 'amount': 100}],
        'tags': [tag.id],
        'image': MINI_PNG_DATA_URI,
        'name': 'Тестовый рецепт',
        'text': 'Описание тестового рецепта',
        'cooking_time': 10,
    }
    payload.update(overrides)
    return payload


def test_tags_list_returns_all_tags(api_client, tag):
    TagFactory()
    TagFactory()

    response = api_client.get('/api/tags/')

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 3


def test_tag_detail_returns_tag(api_client, tag):
    response = api_client.get(f'/api/tags/{tag.id}/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == tag.id
    assert response.data['name'] == tag.name
    assert response.data['slug'] == tag.slug


def test_tag_detail_nonexistent_returns_404(api_client, db):
    response = api_client.get('/api/tags/99999/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_tags_post_method_not_allowed(api_client, db):
    response = api_client.post('/api/tags/', {}, format='json')

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_ingredients_list_returns_all(api_client, ingredient):
    IngredientFactory()

    response = api_client.get('/api/ingredients/')

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 2


def test_ingredient_detail_returns_ingredient(api_client, ingredient):
    response = api_client.get(f'/api/ingredients/{ingredient.id}/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == ingredient.id
    assert response.data['name'] == ingredient.name
    assert response.data['measurement_unit'] == ingredient.measurement_unit


def test_ingredient_detail_nonexistent_returns_404(api_client, db):
    response = api_client.get('/api/ingredients/99999/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_ingredients_filter_by_name_startswith(api_client, db):
    IngredientFactory(name='Сахар', measurement_unit='г')
    IngredientFactory(name='Сахарная пудра', measurement_unit='г')
    IngredientFactory(name='Соль', measurement_unit='г')

    response = api_client.get('/api/ingredients/?name=Сах')

    assert response.status_code == status.HTTP_200_OK
    names = {item['name'] for item in response.data}
    assert names == {'Сахар', 'Сахарная пудра'}


def test_ingredients_filter_is_case_sensitive(api_client, db):
    IngredientFactory(name='Сахар', measurement_unit='г')

    response = api_client.get('/api/ingredients/?name=сахар')

    assert response.status_code == status.HTTP_200_OK
    assert response.data == []


def test_recipes_list_pagination(api_client, user):
    RecipeFactory.create_batch(7, author=user)

    response = api_client.get('/api/recipes/')

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data.keys()) == {'count', 'next', 'previous', 'results'}
    assert response.data['count'] == 7
    assert len(response.data['results']) == 6


def test_recipes_list_filter_by_author(api_client, user, another_user):
    RecipeFactory.create_batch(2, author=user)
    RecipeFactory(author=another_user)

    response = api_client.get(f'/api/recipes/?author={user.id}')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 2
    assert {r['author']['id'] for r in response.data['results']} == {user.id}


def test_recipes_list_filter_by_tags_or_logic(api_client, user):
    tag_a = TagFactory()
    tag_b = TagFactory()
    RecipeFactory(author=user, tags=[tag_a])
    RecipeFactory(author=user, tags=[tag_b])
    RecipeFactory(author=user)  # без тегов

    response = api_client.get(
        f'/api/recipes/?tags={tag_a.slug}&tags={tag_b.slug}',
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 2


def test_recipes_list_is_favorited_anon_returns_empty(api_client, recipe):
    response = api_client.get('/api/recipes/?is_favorited=1')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 0


def test_recipes_list_is_favorited_by_user(
        auth_client, user, recipe, favorite,
):
    response = auth_client.get('/api/recipes/?is_favorited=1')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == recipe.id
    assert response.data['results'][0]['is_favorited'] is True


def test_recipes_list_is_in_shopping_cart_by_user(
        auth_client, user, recipe, shopping_cart,
):
    response = auth_client.get('/api/recipes/?is_in_shopping_cart=1')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert response.data['results'][0]['is_in_shopping_cart'] is True


def test_recipe_detail_anon_flags_false(api_client, recipe):
    response = api_client.get(f'/api/recipes/{recipe.id}/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == recipe.id
    assert response.data['is_favorited'] is False
    assert response.data['is_in_shopping_cart'] is False


def test_recipe_detail_nonexistent_returns_404(api_client, db):
    response = api_client.get('/api/recipes/99999/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_recipe_returns_201(auth_client, user, tag, ingredient):
    payload = _recipe_create_payload(tag, ingredient, name='Мой новый рецепт')

    response = auth_client.post('/api/recipes/', payload, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['name'] == 'Мой новый рецепт'
    assert response.data['cooking_time'] == 10
    assert response.data['author']['id'] == user.id
    assert len(response.data['tags']) == 1
    assert len(response.data['ingredients']) == 1
    assert response.data['ingredients'][0]['id'] == ingredient.id
    assert response.data['ingredients'][0]['amount'] == 100

    recipe = Recipe.objects.get(id=response.data['id'])
    assert recipe.author_id == user.id
    assert recipe.recipe_ingredients.count() == 1
    assert recipe.tags.count() == 1


def test_create_recipe_without_ingredients_returns_400(
        auth_client, tag, ingredient,
):
    payload = _recipe_create_payload(tag, ingredient, ingredients=[])

    response = auth_client.post('/api/recipes/', payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'ingredients' in response.data


def test_create_recipe_with_duplicate_ingredients_returns_400(
        auth_client, tag, ingredient,
):
    payload = _recipe_create_payload(
        tag, ingredient,
        ingredients=[
            {'id': ingredient.id, 'amount': 10},
            {'id': ingredient.id, 'amount': 20},
        ],
    )

    response = auth_client.post('/api/recipes/', payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'ingredients' in response.data


def test_create_recipe_with_nonexistent_ingredient_returns_400(
        auth_client, tag, ingredient,
):
    payload = _recipe_create_payload(
        tag, ingredient,
        ingredients=[{'id': 99999, 'amount': 10}],
    )

    response = auth_client.post('/api/recipes/', payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'ingredients' in response.data


def test_create_recipe_without_tags_returns_400(auth_client, tag, ingredient):
    payload = _recipe_create_payload(tag, ingredient, tags=[])

    response = auth_client.post('/api/recipes/', payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'tags' in response.data


def test_create_recipe_cooking_time_zero_returns_400(
        auth_client, tag, ingredient,
):
    payload = _recipe_create_payload(tag, ingredient, cooking_time=0)

    response = auth_client.post('/api/recipes/', payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'cooking_time' in response.data


def test_create_recipe_invalid_image_returns_400(auth_client, tag, ingredient):
    payload = _recipe_create_payload(tag, ingredient, image='not-a-data-uri')

    response = auth_client.post('/api/recipes/', payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'image' in response.data


def test_create_recipe_anon_returns_401(api_client, tag, ingredient):
    payload = _recipe_create_payload(tag, ingredient)

    response = api_client.post('/api/recipes/', payload, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_recipe_by_author_returns_200(auth_client, user):
    recipe = RecipeFactory(author=user)

    response = auth_client.patch(
        f'/api/recipes/{recipe.id}/',
        {'name': 'Обновлённое имя'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == 'Обновлённое имя'
    recipe.refresh_from_db()
    assert recipe.name == 'Обновлённое имя'


def test_update_recipe_by_another_user_returns_403(
        another_user_client, recipe,
):
    response = another_user_client.patch(
        f'/api/recipes/{recipe.id}/',
        {'name': 'Взлом'},
        format='json',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    recipe.refresh_from_db()
    assert recipe.name != 'Взлом'


def test_update_recipe_anon_returns_401(api_client, recipe):
    response = api_client.patch(
        f'/api/recipes/{recipe.id}/',
        {'name': 'Взлом'},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_recipe_without_image_keeps_old_image(auth_client, user):
    recipe = RecipeFactory(author=user)
    old_image_name = recipe.image.name

    response = auth_client.patch(
        f'/api/recipes/{recipe.id}/',
        {'name': 'Новое имя'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    recipe.refresh_from_db()
    assert recipe.image.name == old_image_name


def test_delete_recipe_by_author_returns_204(auth_client, user):
    recipe = RecipeFactory(author=user)
    recipe_id = recipe.id

    response = auth_client.delete(f'/api/recipes/{recipe_id}/')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Recipe.objects.filter(id=recipe_id).count() == 0


def test_delete_recipe_by_another_user_returns_403(another_user_client, recipe):
    recipe_id = recipe.id

    response = another_user_client.delete(f'/api/recipes/{recipe_id}/')

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Recipe.objects.filter(id=recipe_id).count() == 1


def test_delete_recipe_anon_returns_401(api_client, recipe):
    response = api_client.delete(f'/api/recipes/{recipe.id}/')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_link_returns_short_link(api_client, recipe):
    response = api_client.get(f'/api/recipes/{recipe.id}/get-link/')

    assert response.status_code == status.HTTP_200_OK
    assert 'short-link' in response.data
    assert response.data['short-link'].endswith(f'/s/{recipe.short_code}')


def test_get_link_nonexistent_returns_404(api_client, db):
    response = api_client.get('/api/recipes/99999/get-link/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_short_link_redirects_to_spa_recipe_page(api_client, recipe):
    response = api_client.get(f'/s/{recipe.short_code}/')

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == f'/recipes/{recipe.id}'


def test_short_link_unknown_code_returns_404(api_client, db):
    response = api_client.get('/s/unknown_code_xx/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_add_favorite_returns_201_with_minified(auth_client, user, recipe):
    response = auth_client.post(f'/api/recipes/{recipe.id}/favorite/')

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['id'] == recipe.id
    assert response.data['name'] == recipe.name
    assert response.data['cooking_time'] == recipe.cooking_time
    assert Favorite.objects.filter(user=user, recipe=recipe).count() == 1


def test_add_favorite_twice_returns_400(auth_client, user, recipe):
    auth_client.post(f'/api/recipes/{recipe.id}/favorite/')

    response = auth_client.post(f'/api/recipes/{recipe.id}/favorite/')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_remove_favorite_returns_204(auth_client, user, recipe, favorite):
    response = auth_client.delete(f'/api/recipes/{recipe.id}/favorite/')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Favorite.objects.filter(user=user, recipe=recipe).count() == 0


def test_remove_favorite_when_not_favorited_returns_400(
        auth_client, user, recipe,
):
    response = auth_client.delete(f'/api/recipes/{recipe.id}/favorite/')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_add_favorite_anon_returns_401(api_client, recipe):
    response = api_client.post(f'/api/recipes/{recipe.id}/favorite/')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_add_favorite_nonexistent_recipe_returns_404(auth_client, user):
    response = auth_client.post('/api/recipes/99999/favorite/')

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_add_to_cart_returns_201_with_minified(auth_client, user, recipe):
    response = auth_client.post(f'/api/recipes/{recipe.id}/shopping_cart/')

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['id'] == recipe.id
    assert response.data['name'] == recipe.name
    assert ShoppingCart.objects.filter(user=user, recipe=recipe).count() == 1


def test_add_to_cart_twice_returns_400(auth_client, user, recipe):
    auth_client.post(f'/api/recipes/{recipe.id}/shopping_cart/')

    response = auth_client.post(f'/api/recipes/{recipe.id}/shopping_cart/')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_remove_from_cart_returns_204(
        auth_client, user, recipe, shopping_cart,
):
    response = auth_client.delete(f'/api/recipes/{recipe.id}/shopping_cart/')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert ShoppingCart.objects.filter(user=user, recipe=recipe).count() == 0


def test_remove_from_cart_when_not_added_returns_400(
        auth_client, user, recipe,
):
    response = auth_client.delete(f'/api/recipes/{recipe.id}/shopping_cart/')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_add_to_cart_anon_returns_401(api_client, recipe):
    response = api_client.post(f'/api/recipes/{recipe.id}/shopping_cart/')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_download_shopping_cart_empty_returns_placeholder(auth_client, user):
    response = auth_client.get('/api/recipes/download_shopping_cart/')

    assert response.status_code == status.HTTP_200_OK
    assert response['Content-Type'] == 'text/plain; charset=utf-8'
    assert 'attachment' in response['Content-Disposition']
    assert response.content.decode('utf-8') == 'Список покупок пуст.'


def test_download_shopping_cart_sums_ingredients(
        auth_client, user, tag, ingredient,
):
    sugar = IngredientFactory(name='Сахар', measurement_unit='г')
    recipe_1 = RecipeFactory(author=user)
    recipe_2 = RecipeFactory(author=user)
    recipe_1.recipe_ingredients.create(ingredient=sugar, amount=100)
    recipe_2.recipe_ingredients.create(ingredient=sugar, amount=50)
    auth_client.post(f'/api/recipes/{recipe_1.id}/shopping_cart/')
    auth_client.post(f'/api/recipes/{recipe_2.id}/shopping_cart/')

    response = auth_client.get('/api/recipes/download_shopping_cart/')

    assert response.status_code == status.HTTP_200_OK
    body = response.content.decode('utf-8')
    assert 'Сахар (г) — 150' in body


def test_download_shopping_cart_anon_returns_401(api_client, db):
    response = api_client.get('/api/recipes/download_shopping_cart/')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
def test_author_is_subscribed_true_for_subscriber(
        auth_client, user, another_user,
):
    recipe = RecipeFactory(author=another_user)
    FollowFactory(user=user, author=another_user)

    response = auth_client.get(f'/api/recipes/{recipe.id}/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['author']['id'] == another_user.id
    assert response.data['author']['is_subscribed'] is True


@pytest.mark.integration
def test_is_favorited_true_after_favorite_action(auth_client, user, recipe):
    auth_client.post(f'/api/recipes/{recipe.id}/favorite/')

    response = auth_client.get(f'/api/recipes/{recipe.id}/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['is_favorited'] is True
