from rest_framework import serializers
from .models import Ingredient, Formula, FormulaItem

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
        
class FormulaItemSerializer(serializers.ModelSerializer):
    ingredient = IngredientListSerializer(read_only=True)
    ingredient_id = serializers.IntegerField(write_only=True)
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    safety_level = serializers.CharField(source='ingredient.safety_level', read_only=True)
    
    class Meta:
        model = FormulaItem
        fields = [
            'id', 'ingredient', 'ingredient_id', 'ingredient_name',
            'dose_value', 'dose_unit', 'notes', 'order', 'safety_level'
        ]
    
    def validate_ingredient_id(self, value):
        """Ensure ingredient exists"""
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError("Ingredient does not exist")
        return value


class FormulaListSerializer(serializers.ModelSerializer):
    """Lightweight for formula list"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    item_count = serializers.IntegerField(source='ingredient_count', read_only=True)
    compliance_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Formula
        fields = [
            'id', 'name', 'description', 'region', 
            'owner_username', 'item_count', 
            'compliance_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['owner_username', 'created_at', 'updated_at']
    
    def get_compliance_status(self, obj):
        """Quick compliance status for list view"""
        if obj.items.count() == 0:
            return {'status': 'EMPTY', 'badge_color': '#757575'}
        
        has_risk = False
        has_caution = False
        
        for item in obj.items.all():
            level = item.ingredient.safety_level
            if level == 'RISK':
                has_risk = True
                break
            elif level == 'CAUTION':
                has_caution = True
        
        if has_risk:
            return {'status': 'STOP', 'badge_color': '#f44336'}
        elif has_caution:
            return {'status': 'WARNING', 'badge_color': '#ff9800'}
        else:
            return {'status': 'APPROVED', 'badge_color': '#4caf50'}


class FormulaDetailSerializer(serializers.ModelSerializer):
    """Full details with all items"""
    items = FormulaItemSerializer(many=True, read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    total_weight = serializers.FloatField(source='total_weight_mg', read_only=True)
    item_count = serializers.IntegerField(source='ingredient_count', read_only=True)
    
    class Meta:
        model = Formula
        fields = [
            'id', 'name', 'description', 'region',
            'owner_username', 'items', 'total_weight', 'item_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['owner_username', 'created_at', 'updated_at']
        
class ComplianceIssueSerializer(serializers.Serializer):
    """Serializer for individual compliance issues"""
    ingredient_id = serializers.IntegerField()
    ingredient = serializers.CharField()
    dose = serializers.CharField()
    category = serializers.CharField()
    severity = serializers.CharField()
    level = serializers.CharField()
    safety_info = serializers.CharField()
    message = serializers.CharField()
    action = serializers.CharField()


class ComplianceResultSerializer(serializers.Serializer):
    """Serializer for compliance check results"""
    status = serializers.CharField()
    status_message = serializers.CharField()
    can_proceed = serializers.BooleanField()
    formula_id = serializers.IntegerField()
    formula_name = serializers.CharField()
    region = serializers.CharField()
    total_ingredients = serializers.IntegerField()
    total_weight_mg = serializers.FloatField()
    summary = serializers.DictField()
    issues = ComplianceIssueSerializer(many=True)
    checked_at = serializers.DateTimeField()