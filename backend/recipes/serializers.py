import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

from users.serializers import UserReadSerializer

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


class TagSerializer(serializers.ModelSerializer):
    """Тег: {id, name, slug}."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id',)


class IngredientSerializer(serializers.ModelSerializer):
    """Ингредиент: {id, name, measurement_unit}."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id',)


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Вложенное чтение ингредиента рецепта.

    Ключевое отличие от IngredientSerializer: id — это id ингредиента
    (не id RecipeIngredient). Плюс — поле amount.
    """

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """RecipeMinified: {id, name, image, cooking_time}."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class RecipeListSerializer(serializers.ModelSerializer):
    """RecipeList: полное представление рецепта."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserReadSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = fields

    def get_is_favorited(self, obj: Recipe) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """{id, amount} — input для записи ингредиента в рецепт."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


def _decode_image(data_uri: str) -> ContentFile:
    """Декодирует data:image/...;base64,... → ContentFile для ImageField."""
    if not isinstance(data_uri, str) or not data_uri.startswith('data:image/'):
        raise serializers.ValidationError(
            'Ожидается data-URI вида data:image/png;base64,...'
        )
    if ';base64,' not in data_uri:
        raise serializers.ValidationError(
            'Ожидается base64-кодированное изображение.'
        )
    header, b64_data = data_uri.split(';base64,', 1)
    ext = header.split('/')[-1].lower()
    if ext == 'jpeg':
        ext = 'jpg'
    try:
        decoded = base64.b64decode(b64_data)
    except Exception as exc:
        raise serializers.ValidationError(
            'Не удалось декодировать base64.'
        ) from exc
    filename = f'{uuid.uuid4().hex}.{ext}'
    return ContentFile(decoded, name=filename)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """База для create/update.

    Принимает: ingredients=[{id, amount}], tags=[id], image (base64),
    name, text, cooking_time. Возвращает RecipeList-представление.
    """

    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = serializers.CharField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, value: list[dict]) -> list[dict]:
        if not value:
            raise serializers.ValidationError(
                'Нужен хотя бы один ингредиент.'
            )
        ids = [item['id'] for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        existing = Ingredient.objects.filter(id__in=ids)
        if existing.count() != len(ids):
            raise serializers.ValidationError(
                'Некоторые ингредиенты не существуют.'
            )
        return value

    def validate_tags(self, value: list[Tag]) -> list[Tag]:
        if not value:
            raise serializers.ValidationError('Нужен хотя бы один тег.')
        return value

    def validate_cooking_time(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше 0.'
            )
        return value

    def validate_image(self, value: str) -> str:
        if not value.startswith('data:image/'):
            raise serializers.ValidationError(
                'Ожидается data-URI вида data:image/png;base64,...'
            )
        if ';base64,' not in value:
            raise serializers.ValidationError(
                'Ожидается base64-кодированное изображение.'
            )
        return value

    def create(self, validated_data: dict) -> Recipe:
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        image_data = validated_data.pop('image')
        author = self.context['request'].user

        recipe = Recipe.objects.create(
            author=author,
            image=_decode_image(image_data),
            **validated_data,
        )
        recipe.tags.set(tags_data)
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['id'],
                amount=item['amount'],
            )
            for item in ingredients_data
        ])
        return recipe

    def update(self, instance: Recipe, validated_data: dict) -> Recipe:
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        image_data = validated_data.pop('image', None)

        if image_data:
            instance.image = _decode_image(image_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            RecipeIngredient.objects.bulk_create([
                RecipeIngredient(
                    recipe=instance,
                    ingredient_id=item['id'],
                    amount=item['amount'],
                )
                for item in ingredients_data
            ])

        return instance

    def to_representation(self, instance: Recipe) -> dict:
        return RecipeListSerializer(instance, context=self.context).data


class RecipeCreateSerializer(RecipeWriteSerializer):
    """POST /api/recipes/ — image обязательна."""

    image = serializers.CharField(required=True)


class RecipeUpdateSerializer(RecipeWriteSerializer):
    """PATCH/PUT /api/recipes/{id}/ — image не обязательна."""

    image = serializers.CharField(required=False)
