from rest_framework import serializers

from .models import Recipe, GroceryList


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'title', 'content', 'parsed_recipe', 'user']

class GroceryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroceryList
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
