"""Тесты утилит: generate_short_code, _decode_image, load_ingredients."""

import base64
from io import StringIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management import call_command
import pytest
from rest_framework import serializers

from recipes.models import (
    Ingredient,
    Recipe,
    generate_short_code as generate_short_code_func,
)
from recipes.serializers import _decode_image
from tests.factories.recipes import MINI_PNG_B64


def test_generate_short_code_returns_str():
    code = generate_short_code_func()

    assert isinstance(code, str)


def test_generate_short_code_has_length_6():
    code = generate_short_code_func()

    assert len(code) == 6


def test_generate_short_code_produces_unique_values():
    codes = {generate_short_code_func() for _ in range(50)}

    assert len(codes) == 50


def test_generate_short_code_uses_only_base64url_chars():
    allowed = set(
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    )

    for _ in range(20):
        code = generate_short_code_func()
        assert set(code).issubset(allowed)


def test_recipe_save_reuses_existing_short_code(db, user):
    recipe = Recipe.objects.create(
        author=user,
        name='Рецепт',
        image=ContentFile(b'x', name='test.png'),
        text='text',
        cooking_time=5,
    )
    original_code = recipe.short_code

    recipe.name = 'Изменённый'
    recipe.save()

    recipe.refresh_from_db()
    assert recipe.short_code == original_code


def test_recipe_save_generates_short_code_if_empty(db, user):
    recipe = Recipe.objects.create(
        author=user,
        name='Рецепт',
        image=ContentFile(b'x', name='test.png'),
        text='text',
        cooking_time=5,
    )

    assert recipe.short_code != ''


def test_decode_image_returns_contentfile_with_png_extension():
    data_uri = f'data:image/png;base64,{MINI_PNG_B64}'

    result = _decode_image(data_uri)

    assert isinstance(result, ContentFile)
    assert result.name.endswith('.png')


def test_decode_image_jpeg_extension_is_normalized_to_jpg():
    data_uri = f'data:image/jpeg;base64,{MINI_PNG_B64}'

    result = _decode_image(data_uri)

    assert result.name.endswith('.jpg')


def test_decode_image_invalid_prefix_raises_validation_error():
    with pytest.raises(serializers.ValidationError):
        _decode_image('not-a-data-uri')


def test_decode_image_missing_base64_marker_raises_validation_error():
    with pytest.raises(serializers.ValidationError):
        _decode_image('data:image/png,abc')


def test_decode_image_invalid_base64_raises_validation_error():
    with pytest.raises(serializers.ValidationError):
        _decode_image('data:image/png;base64,!!!not-base64!!!')


def test_decode_image_content_matches_original():
    data_uri = f'data:image/png;base64,{MINI_PNG_B64}'

    result = _decode_image(data_uri)

    assert result.read() == base64.b64decode(MINI_PNG_B64)


def _write_csv(tmp_path: Path, rows: list[tuple[str, str]]) -> Path:
    """Пишет CSV name,measurement_unit без заголовка."""
    path = tmp_path / 'ingredients.csv'
    path.write_text('\n'.join(f'{n},{u}' for n, u in rows), encoding='utf-8')
    return path


@pytest.mark.django_db
def test_load_ingredients_creates_rows(tmp_path):
    path = _write_csv(
        tmp_path,
        [
            ('Сахар', 'г'),
            ('Соль', 'г'),
            ('Молоко', 'мл'),
        ],
    )

    call_command('load_ingredients', path=str(path))

    assert Ingredient.objects.count() == 3
    assert (
        Ingredient.objects.filter(
            name='Сахар',
            measurement_unit='г',
        ).exists()
        is True
    )


@pytest.mark.django_db
def test_load_ingredients_is_idempotent(tmp_path):
    path = _write_csv(
        tmp_path,
        [
            ('Сахар', 'г'),
            ('Соль', 'г'),
        ],
    )

    call_command('load_ingredients', path=str(path))
    call_command('load_ingredients', path=str(path))

    assert Ingredient.objects.count() == 2


@pytest.mark.django_db
def test_load_ingredients_deduplicates_within_csv(tmp_path):
    path = _write_csv(
        tmp_path,
        [
            ('Сахар', 'г'),
            ('Сахар', 'г'),
            ('Соль', 'г'),
        ],
    )

    call_command('load_ingredients', path=str(path))

    assert Ingredient.objects.count() == 2


@pytest.mark.django_db
def test_load_ingredients_missing_file_prints_error(tmp_path):
    stderr = StringIO()

    call_command(
        'load_ingredients',
        path=str(tmp_path / 'nonexistent.csv'),
        stderr=stderr,
    )

    assert 'Файл не найден' in stderr.getvalue()
    assert Ingredient.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.slow
def test_load_ingredients_from_repo_csv_creates_many_rows():
    """Маркер slow — реальный CSV 2000+ строк."""
    from django.conf import settings

    csv_path = Path(settings.BASE_DIR) / 'data' / 'ingredients.csv'
    if not csv_path.exists():
        pytest.skip('data/ingredients.csv не найден')

    call_command('load_ingredients', path=str(csv_path))

    assert Ingredient.objects.count() > 2000


@pytest.mark.django_db
def test_load_ingredients_skips_rows_with_one_column(tmp_path):
    path = tmp_path / 'ing.csv'
    path.write_text('Сахар\nСоль,г', encoding='utf-8')

    call_command('load_ingredients', path=str(path))

    assert Ingredient.objects.count() == 1
    assert Ingredient.objects.filter(name='Соль').exists() is True


@pytest.mark.django_db
def test_load_ingredients_skips_rows_with_empty_fields(tmp_path):
    path = tmp_path / 'ing.csv'
    path.write_text(',г\nСоль,\nСахар,г', encoding='utf-8')

    call_command('load_ingredients', path=str(path))

    assert Ingredient.objects.count() == 1
    assert Ingredient.objects.filter(name='Сахар').exists() is True
