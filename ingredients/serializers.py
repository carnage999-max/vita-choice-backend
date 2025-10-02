from rest_framework import serializers
from .models import Ingredient

class IngredientListSerializer(serializers.ModelSerializer):
    """Lightweight for list views"""
    safety_level = serializers.CharField(read_only=True)
    safety_color = serializers.CharField(read_only=True)
    
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'category', 'source', 'safety', 'safety_level', 'safety_color']


class IngredientDetailSerializer(serializers.ModelSerializer):
    """Full details for single ingredient"""
    safety_level = serializers.CharField(read_only=True)
    safety_color = serializers.CharField(read_only=True)
    
    class Meta:
        model = Ingredient
        fields = [
            'id', 'name', 'category', 'source', 'safety', 'evidence',
            'safety_level', 'safety_color', 'created_at', 'updated_at'
        ]