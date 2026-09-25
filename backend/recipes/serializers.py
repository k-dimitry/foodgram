from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from users.serializers import UserReadSerializer

from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)


class TagSerializer(serializers.ModelSerializer):
    """Тег: {id, name, slug}."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Ингредиент: {id, name, measurement_unit}."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Вложенный ингредиент рецепта: чтение и запись."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all(),
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True,
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True,
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    """RecipeList: полное представление рецепта."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserReadSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

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


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Создание и обновление рецепта."""

    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField(required=False)

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

    def validate(self, attrs: dict) -> dict:
        image = attrs.get('image')
        image_passed = 'image' in self.initial_data

        if self.instance is None:
            if not image:
                raise serializers.ValidationError({
                    'image': 'Это поле обязательно.'
                })
        elif image_passed and not image:
            raise serializers.ValidationError({
                'image': 'Поле не может быть пустым.'
            })

        ingredients = attrs.get('ingredients') or []
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хотя бы один ингредиент.'
            })
        ingredient_ids = [item['ingredient'].pk for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты не должны повторяться.'
            })

        tags = attrs.get('tags') or []
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужен хотя бы один тег.'
            })
        tag_ids = [tag.pk for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError({
                'tags': 'Теги не должны повторяться.'
            })

        return attrs

    @transaction.atomic
    def create(self, validated_data: dict) -> Recipe:
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author = self.context['request'].user

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance: Recipe, validated_data: dict) -> Recipe:
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.recipe_ingredients.all().delete()
        self._save_ingredients(instance, ingredients_data)
        return instance

    @staticmethod
    def _save_ingredients(
        recipe: Recipe,
        ingredients_data: list[dict],
    ) -> None:
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount'],
            )
            for item in ingredients_data
        ])

    def to_representation(self, instance: Recipe) -> dict:
        request = self.context.get('request')
        user = request.user if request else None
        annotated = Recipe.objects.with_user_flags(user).get(pk=instance.pk)
        return RecipeListSerializer(annotated, context=self.context).data
