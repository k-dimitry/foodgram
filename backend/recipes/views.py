from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Ingredient, Tag
from .serializers import IngredientSerializer, TagSerializer


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
