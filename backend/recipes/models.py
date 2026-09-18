import secrets

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Tag(models.Model):
    """Тег для классификации рецептов."""

    name = models.CharField(
        'название',
        max_length=32,
        unique=True,
    )
    slug = models.SlugField(
        'слаг',
        max_length=32,
        unique=True,
        allow_unicode=False,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Ингредиент: продукт + единица измерения."""

    name = models.CharField(
        'название',
        max_length=128,
    )
    measurement_unit = models.CharField(
        'единица измерения',
        max_length=64,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name', 'id')
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.name} ({self.measurement_unit})'


def generate_short_code() -> str:
    """Генерирует короткий код для ссылки на рецепт (6 символов base64url)."""
    return secrets.token_urlsafe(4)


class Recipe(models.Model):
    """Рецепт: блюдо с ингредиентами, тегами и автором."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='автор',
    )
    name = models.CharField(
        'название',
        max_length=256,
    )
    image = models.ImageField(
        'картинка',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        'описание',
    )
    cooking_time = models.PositiveIntegerField(
        'время приготовления (мин)',
        validators=(MinValueValidator(1),),
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='ингредиенты',
    )
    pub_date = models.DateTimeField(
        'дата публикации',
        auto_now_add=True,
    )
    short_code = models.CharField(
        'короткий код',
        max_length=16,
        unique=True,
        db_index=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        constraints = [
            models.CheckConstraint(
                check=models.Q(cooking_time__gte=1),
                name='recipe_cooking_time_gte_1',
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.short_code:
            for _ in range(10):
                code = generate_short_code()
                if not Recipe.objects.filter(short_code=code).exists():
                    self.short_code = code
                    break
            else:
                raise RuntimeError(
                    'Не удалось сгенерировать уникальный short_code за 10 попыток'
                )
        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    """Связь рецепта и ингредиента с указанием количества."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name='recipe_ingredients',
        verbose_name='ингредиент',
    )
    amount = models.PositiveIntegerField(
        'количество',
        validators=(MinValueValidator(1),),
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            ),
            models.CheckConstraint(
                check=models.Q(amount__gte=1),
                name='recipe_ingredient_amount_gte_1',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.recipe.name}: {self.ingredient.name} — {self.amount}'
