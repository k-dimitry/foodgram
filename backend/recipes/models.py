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
