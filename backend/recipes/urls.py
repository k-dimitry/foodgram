from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, TagViewSet

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')

urlpatterns = router.urls
