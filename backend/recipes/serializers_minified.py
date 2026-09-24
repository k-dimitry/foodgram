from rest_framework import serializers

from .models import Recipe


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """RecipeMinified: {id, name, image, cooking_time}."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields
