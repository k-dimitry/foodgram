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
