from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Ingredient
from .serializers import IngredientListSerializer, IngredientDetailSerializer

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Ingredient API endpoints
    
    list: GET /api/ingredients/
    retrieve: GET /api/ingredients/{id}/
    search: GET /api/ingredients/?search=vitamin
    filter: GET /api/ingredients/?category=Vitamins&safety_level=SAFE
    """
    queryset = Ingredient.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'category', 'source']
    ordering_fields = ['name', 'category', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return IngredientListSerializer
        return IngredientDetailSerializer
    
    def get_queryset(self):
        queryset = Ingredient.objects.all()
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__icontains=category)
        
        # Filter by source
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source__icontains=source)
        
        # Filter by safety text
        safety = self.request.query_params.get('safety')
        if safety:
            queryset = queryset.filter(safety__icontains=safety)
        
        # Exclude high-risk ingredients
        exclude_risk = self.request.query_params.get('exclude_risk')
        if exclude_risk == 'true':
            queryset = queryset.exclude(
                safety__icontains='Restricted'
            ).exclude(
                safety__icontains='Controlled'
            ).exclude(
                safety__icontains='High-Risk'
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get unique categories"""
        categories = Ingredient.objects.values_list('category', flat=True).distinct()
        categories = sorted([c for c in categories if c])
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def sources(self, request):
        """Get unique sources"""
        sources = Ingredient.objects.values_list('source', flat=True).distinct()
        sources = sorted([s for s in sources if s])
        return Response(sources)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get ingredient statistics"""
        total = Ingredient.objects.count()
        
        # Count by safety level (manual iteration since it's a property)
        safe_count = 0
        caution_count = 0
        risk_count = 0
        
        for ingredient in Ingredient.objects.all():
            level = ingredient.safety_level
            if level == 'SAFE':
                safe_count += 1
            elif level == 'CAUTION':
                caution_count += 1
            elif level == 'RISK':
                risk_count += 1
        
        return Response({
            'total': total,
            'by_safety_level': {
                'safe': safe_count,
                'caution': caution_count,
                'risk': risk_count,
            },
            'categories': Ingredient.objects.values('category').distinct().count(),
        })