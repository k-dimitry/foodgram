from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.serializers_minified import RecipeMinifiedSerializer

from .models import Follow


User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    """Пользователь: чтение (GET /users/, /users/{id}/, /users/me/)."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj: User) -> bool:
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Follow.objects.filter(user=request.user, author=obj).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    """PUT /api/users/me/avatar/ — загрузка аватара (base64 в JSON)."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class UserWithRecipesSerializer(UserReadSerializer):
    """UserWithRecipes: UserRead + recipes (с ограничением) + recipes_count."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserReadSerializer.Meta):
        fields = UserReadSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = fields

    def _get_recipes_limit(self) -> int | None:
        """Читает ?recipes_limit=N из query-параметров."""
        request = self.context.get('request')
        if not request:
            return None
        value = request.query_params.get('recipes_limit')
        if not value:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def get_recipes(self, obj: User) -> list[dict]:
        qs = obj.recipes.all().order_by('-pub_date')
        limit = self._get_recipes_limit()
        if limit is not None and limit < 0:
            limit = 0
        if limit is not None:
            qs = qs[:limit]
        return RecipeMinifiedSerializer(
            qs,
            many=True,
            context=self.context,
        ).data

    def get_recipes_count(self, obj: User) -> int:
        return obj.recipes.count()
