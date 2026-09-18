from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка тегов."""

    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    ordering = ('id',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка ингредиентов."""

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    ordering = ('id',)


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для ингредиентов рецепта."""

    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка рецептов."""

    list_display = ('id', 'name', 'author', 'pub_date')
    list_filter = ('tags',)
    search_fields = ('name', 'author__username', 'author__email')
    readonly_fields = ('pub_date', 'short_code')
    inlines = (RecipeIngredientInline,)
    filter_horizontal = ('tags',)
    ordering = ('-pub_date',)
