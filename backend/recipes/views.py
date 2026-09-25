from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from users.permissions import IsAuthorOrReadOnly

from .filters import RecipeFilter
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from .serializers import (
    IngredientSerializer,
    RecipeListSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)
from .serializers_minified import RecipeMinifiedSerializer


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
    """Рецепты: CRUD + фильтры + избранное/корзина/шорт-линк."""

    queryset = Recipe.objects.select_related('author').prefetch_related(
        'recipe_ingredients__ingredient',
        'tags',
    )
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeListSerializer

    def get_queryset(self):
        return super().get_queryset().with_user_flags(self.request.user)

    def _handle_user_recipe_action(self, request, recipe, model):
        """Общая логика POST/DELETE для favorite и shopping_cart.

        POST — создать связь, DELETE — удалить.
        """
        if request.method == 'POST':
            _, created = model.objects.get_or_create(
                user=request.user,
                recipe=recipe,
            )
            if not created:
                return Response(
                    {'detail': 'Рецепт уже добавлен.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request},
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        deleted, _ = model.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Рецепт не найден.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

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

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='favorite',
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        """POST — добавить в избранное, DELETE — убрать."""
        recipe = self.get_object()
        return self._handle_user_recipe_action(request, recipe, Favorite)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        """POST — добавить в список покупок, DELETE — убрать."""
        recipe = self.get_object()
        return self._handle_user_recipe_action(
            request,
            recipe,
            ShoppingCart,
        )

    @action(
        detail=False,
        methods=('get',),
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """GET /api/recipes/download_shopping_cart/ — txt со списком."""
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in_shopping_carts__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name', 'ingredient__measurement_unit')
        )

        lines = [
            f'{item["ingredient__name"]} '
            f'({item["ingredient__measurement_unit"]}) — '
            f'{item["total"]}'
            for item in ingredients
        ]

        content = '\n'.join(lines) if lines else 'Список покупок пуст.'

        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


class ShortLinkRedirectView(View):
    """GET /s/<short_code>/ — редирект на SPA-роут страницы рецепта."""

    def get(self, request, short_code: str):
        try:
            recipe = Recipe.objects.get(short_code=short_code)
        except Recipe.DoesNotExist:
            return redirect('/404')
        return redirect(f'/recipes/{recipe.id}')
