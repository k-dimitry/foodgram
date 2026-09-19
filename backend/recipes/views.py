from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status

from users.permissions import IsAuthorOrReadOnly

from .models import Ingredient, Tag, Recipe
from .serializers import (
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeListSerializer,
    RecipeUpdateSerializer,
    TagSerializer,
)


class TagViewSet(ReadOnlyModelViewSet):
    """Теги: только чтение."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Ингредиенты: только чтение + фильтр по name."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            qs = qs.filter(name__startswith=name)
        return qs


class RecipeViewSet(ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        if self.action in ('update', 'partial_update'):
            return RecipeUpdateSerializer
        return RecipeListSerializer

    def get_queryset(self):
        qs = Recipe.objects.select_related('author').prefetch_related(
            'recipe_ingredients__ingredient',
            'tags',
        )
        params = self.request.query_params

        if params.get('is_favorited') == '1':
            if self.request.user.is_authenticated:
                qs = qs.filter(favorited_by__user=self.request.user)
            else:
                qs = qs.none()

        if params.get('is_in_shopping_cart') == '1':
            if self.request.user.is_authenticated:
                qs = qs.filter(in_shopping_carts__user=self.request.user)
            else:
                qs = qs.none()

        author_id = params.get('author')
        if author_id:
            qs = qs.filter(author_id=author_id)

        tags = params.getlist('tags')
        if tags:
            qs = qs.filter(tags__slug__in=tags).distinct()

        return qs

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
        permission_classes=(AllowAny,),
    )
    def get_link(self, request, pk=None):
        """GET /api/recipes/{id}/get-link/ — короткая ссылка на рецепт."""
        recipe = self.get_object()
        link = request.build_absolute_uri(f'/s/{recipe.short_code}')
        return Response({'short-link': link}, status=status.HTTP_200_OK)


class ShortLinkRedirectView(View):
    """GET /s/<short_code>/ — редирект на SPA-роут страницы рецепта."""

    def get(self, request, short_code: str):
        recipe = get_object_or_404(Recipe, short_code=short_code)
        return redirect(f'/recipes/{recipe.id}')
