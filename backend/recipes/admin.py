from django.contrib import admin
from django.db.models import Count

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка тегов."""

    list_display = ('id', 'name', 'slug', 'recipes_count')
    search_fields = ('name', 'slug')
    ordering = ('id',)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                recipes_count=Count('recipes'),
            )
        )

    @admin.display(description='Рецептов')
    def recipes_count(self, obj: Tag) -> int:
        return obj.recipes_count


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка ингредиентов."""

    list_display = ('id', 'name', 'measurement_unit', 'recipes_count')
    search_fields = ('name',)
    ordering = ('id',)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                recipes_count=Count('recipe_ingredients'),
            )
        )

    @admin.display(description='Рецептов')
    def recipes_count(self, obj: Ingredient) -> int:
        return obj.recipes_count


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для ингредиентов рецепта."""

    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка рецептов."""

    list_display = ('id', 'name', 'author', 'pub_date', 'favorites_count')
    list_filter = ('tags',)
    search_fields = ('name', 'author__username', 'author__email')
    readonly_fields = ('pub_date', 'short_code', 'favorites_count')
    inlines = (RecipeIngredientInline,)
    filter_horizontal = ('tags',)
    ordering = ('-pub_date',)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                favorites_count_annotated=Count('favorited_by'),
            )
        )

    @admin.display(description='В избранном')
    def favorites_count(self, obj: Recipe) -> int:
        return obj.favorites_count_annotated


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка избранного."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    ordering = ('id',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка списков покупок."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    ordering = ('id',)
