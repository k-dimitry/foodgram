from rest_framework import serializers

from .models import Ingredient, Tag


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
