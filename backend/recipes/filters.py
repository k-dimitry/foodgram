"""Фильтры приложения recipes."""

import django_filters

from .models import Recipe


class RecipeFilter(django_filters.FilterSet):
    """Фильтры для рецептов."""

    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug',
    )
    author = django_filters.NumberFilter(
        field_name='author',
    )
    is_favorited = django_filters.NumberFilter(
        method='filter_is_favorited',
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if value != 1:
            return queryset
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        return queryset.filter(favorited_by__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value != 1:
            return queryset
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        return queryset.filter(in_shopping_carts__user=user)
