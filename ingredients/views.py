import csv
from django.http import HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Ingredient
from .serializers import (
    IngredientListSerializer,
    IngredientDetailSerializer,
    FormulaItemSerializer,
    FormulaListSerializer,
    FormulaDetailSerializer,
    ComplianceResultSerializer,
)
from .models import Formula, FormulaItem
from .services.pdf_generator import FormulaSummaryGenerator, SupplementFactsGenerator
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch


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
    search_fields = ["name", "category", "source"]
    ordering_fields = ["name", "category", "created_at"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return IngredientListSerializer
        return IngredientDetailSerializer

    def get_queryset(self):
        queryset = Ingredient.objects.all()

        # Filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__icontains=category)

        # Filter by source
        source = self.request.query_params.get("source")
        if source:
            queryset = queryset.filter(source__icontains=source)

        # Filter by safety text
        safety = self.request.query_params.get("safety")
        if safety:
            queryset = queryset.filter(safety__icontains=safety)

        # Exclude high-risk ingredients
        exclude_risk = self.request.query_params.get("exclude_risk")
        if exclude_risk == "true":
            queryset = (
                queryset.exclude(safety__icontains="Restricted")
                .exclude(safety__icontains="Controlled")
                .exclude(safety__icontains="High-Risk")
            )

        return queryset

    @action(detail=False, methods=["get"])
    def categories(self, request):
        """Get unique categories"""
        categories = Ingredient.objects.values_list("category", flat=True).distinct()
        categories = sorted([c for c in categories if c])
        return Response(categories)

    @action(detail=False, methods=["get"])
    def sources(self, request):
        """Get unique sources"""
        sources = Ingredient.objects.values_list("source", flat=True).distinct()
        sources = sorted([s for s in sources if s])
        return Response(sources)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get ingredient statistics"""
        total = Ingredient.objects.count()

        # Count by safety level (manual iteration since it's a property)
        safe_count = 0
        caution_count = 0
        risk_count = 0

        for ingredient in Ingredient.objects.all():
            level = ingredient.safety_level
            if level == "SAFE":
                safe_count += 1
            elif level == "CAUTION":
                caution_count += 1
            elif level == "RISK":
                risk_count += 1

        return Response(
            {
                "total": total,
                "by_safety_level": {
                    "safe": safe_count,
                    "caution": caution_count,
                    "risk": risk_count,
                },
                "categories": Ingredient.objects.values("category").distinct().count(),
            }
        )


class FormulaViewSet(viewsets.ModelViewSet):
    """
    Formula CRUD operations

    list: GET /api/formulas/
    create: POST /api/formulas/
    retrieve: GET /api/formulas/{id}/
    update: PUT /api/formulas/{id}/
    partial_update: PATCH /api/formulas/{id}/
    destroy: DELETE /api/formulas/{id}/
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return FormulaListSerializer
        return FormulaDetailSerializer

    def get_queryset(self):
        """Only show user's own formulas"""
        return Formula.objects.filter(owner=self.request.user).prefetch_related(
            Prefetch("items", queryset=FormulaItem.objects.select_related("ingredient"))
        )

    def perform_create(self, serializer):
        """Auto-assign current user as owner"""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def add_ingredient(self, request, pk=None):
        """
        Add an ingredient to the formula

        POST /api/formulas/{id}/add_ingredient/
        Body: {
            "ingredient_id": 123,
            "dose_value": 500,
            "dose_unit": "mg",
            "notes": "Optional notes"
        }
        """
        formula = self.get_object()
        serializer = FormulaItemSerializer(data=request.data)

        if serializer.is_valid():
            # Check if ingredient already exists in formula
            ingredient_id = serializer.validated_data["ingredient_id"]
            if FormulaItem.objects.filter(
                formula=formula, ingredient_id=ingredient_id
            ).exists():
                return Response(
                    {"error": "Ingredient already exists in this formula"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save(formula=formula)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["delete"],
        url_path="remove_ingredient/(?P<item_id>[^/.]+)",
    )
    def remove_ingredient(self, request, pk=None, item_id=None):
        """
        Remove an ingredient from the formula

        DELETE /api/formulas/{id}/remove_ingredient/{item_id}/
        """
        formula = self.get_object()

        try:
            item = FormulaItem.objects.get(id=item_id, formula=formula)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FormulaItem.DoesNotExist:
            return Response(
                {"error": "Ingredient not found in this formula"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(
        detail=True, methods=["patch"], url_path="update_ingredient/(?P<item_id>[^/.]+)"
    )
    def update_ingredient(self, request, pk=None, item_id=None):
        """
        Update ingredient dose/notes

        PATCH /api/formulas/{id}/update_ingredient/{item_id}/
        Body: {
            "dose_value": 750,
            "dose_unit": "mg",
            "notes": "Updated notes"
        }
        """
        formula = self.get_object()

        try:
            item = FormulaItem.objects.get(id=item_id, formula=formula)
            serializer = FormulaItemSerializer(item, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except FormulaItem.DoesNotExist:
            return Response(
                {"error": "Ingredient not found in this formula"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        """
        Duplicate a formula

        POST /api/formulas/{id}/duplicate/
        Body: {
            "name": "New formula name (optional)"
        }
        """
        original = self.get_object()

        # Create copy
        new_name = request.data.get("name", f"{original.name} (Copy)")
        new_formula = Formula.objects.create(
            owner=request.user,
            name=new_name,
            description=original.description,
            region=original.region,
        )

        # Copy all items
        for item in original.items.all():
            FormulaItem.objects.create(
                formula=new_formula,
                ingredient=item.ingredient,
                dose_value=item.dose_value,
                dose_unit=item.dose_unit,
                notes=item.notes,
                order=item.order,
            )

        serializer = FormulaDetailSerializer(new_formula)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def check_compliance(self, request, pk=None):
        """
        Check formula compliance against safety regulations

        POST /api/formulas/{id}/check_compliance/

        Response includes:
        - Overall status (APPROVED/WARNING/STOP)
        - List of issues by severity
        - Recommendations for each issue
        - Summary statistics
        """
        formula = self.get_object()

        # Check if formula has ingredients
        if formula.items.count() == 0:
            return Response(
                {
                    "error": "Formula has no ingredients. Add ingredients before checking compliance."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Run compliance check
        result = formula.check_compliance()

        # Add formula metadata
        result["formula_id"] = formula.id
        result["formula_name"] = formula.name
        result["region"] = formula.region
        result["total_weight_mg"] = formula.total_weight_mg()
        result["checked_at"] = timezone.now()

        # Serialize result
        serializer = ComplianceResultSerializer(result)

        # Log compliance check (we'll add audit logs later)
        # For now, just return result

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def compliance_summary(self, request, pk=None):
        """
        Get quick compliance summary without full check

        GET /api/formulas/{id}/compliance_summary/

        Returns just the counts without detailed issues
        """
        formula = self.get_object()

        if formula.items.count() == 0:
            return Response(
                {
                    "status": "EMPTY",
                    "message": "No ingredients in formula",
                    "summary": {"safe": 0, "caution": 0, "risk": 0},
                }
            )

        safe_count = 0
        caution_count = 0
        risk_count = 0

        for item in formula.items.select_related("ingredient").all():
            level = item.ingredient.safety_level
            if level == "SAFE":
                safe_count += 1
            elif level == "CAUTION":
                caution_count += 1
            elif level == "RISK":
                risk_count += 1

        if risk_count > 0:
            status_label = "STOP"
        elif caution_count > 0:
            status_label = "WARNING"
        else:
            status_label = "APPROVED"

        return Response(
            {
                "status": status_label,
                "summary": {
                    "safe": safe_count,
                    "caution": caution_count,
                    "risk": risk_count,
                },
                "total_ingredients": formula.items.count(),
            }
        )

    @action(detail=True, methods=["get"])
    def export_label(self, request, pk=None):
        """
        Export Supplement Facts label as PDF

        GET /api/formulas/{id}/export_label/

        Returns: PDF file
        """
        formula = self.get_object()

        if formula.items.count() == 0:
            return Response(
                {"error": "Formula has no ingredients. Cannot generate label."},
                status=status.HTTP_400_BAD_REQUEST,
        )

        try:
            generator = SupplementFactsGenerator(formula)
            pdf_buffer = generator.generate()
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()

            filename = slugify(formula.name) or "formula"
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="{filename}-supplement-facts.pdf"'
            )
            return response

        except Exception as e:
            return Response(
                {"error": f"Failed to generate PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def export_summary(self, request, pk=None):
        """
        Export simple formula summary as PDF

        GET /api/formulas/{id}/export_summary/

        Returns: PDF file
        """
        formula = self.get_object()

        if formula.items.count() == 0:
            return Response(
                {"error": "Formula has no ingredients."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            generator = FormulaSummaryGenerator(formula)
            pdf_buffer = generator.generate()
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()

            filename = slugify(formula.name) or "formula"
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="{filename}-summary.pdf"'
            )
            return response

        except Exception as e:
            return Response(
                {"error": f"Failed to generate PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def export_csv(self, request, pk=None):
        """
        Export formula as CSV

        GET /api/formulas/{id}/export_csv/

        Returns: CSV file
        """
        formula = self.get_object()

        if formula.items.count() == 0:
            return Response(
                {"error": "Formula has no ingredients."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create CSV
        response = HttpResponse(content_type="text/csv")
        filename = f"{formula.name.replace(' ', '_')}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        # Header
        writer.writerow(
            [
                "Ingredient",
                "Category",
                "Source",
                "Dose Value",
                "Dose Unit",
                "Safety",
                "Safety Level",
                "Notes",
            ]
        )

        # Data
        for item in formula.items.select_related("ingredient").all():
            writer.writerow(
                [
                    item.ingredient.name,
                    item.ingredient.category,
                    item.ingredient.source,
                    item.dose_value,
                    item.dose_unit,
                    item.ingredient.safety,
                    item.ingredient.safety_level,
                    item.notes,
                ]
            )

        return response

    @action(detail=False, methods=["get"])
    def export_all_csv(self, request):
        """
        Export all user's formulas as CSV

        GET /api/formulas/export_all_csv/

        Returns: CSV file with all formulas
        """
        formulas = self.get_queryset()

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="my_formulas.csv"'

        writer = csv.writer(response)

        # Header
        writer.writerow(
            [
                "Formula Name",
                "Formula Description",
                "Region",
                "Ingredient",
                "Category",
                "Dose Value",
                "Dose Unit",
                "Safety Level",
                "Created At",
            ]
        )

        # Data
        for formula in formulas:
            for item in formula.items.select_related("ingredient").all():
                writer.writerow(
                    [
                        formula.name,
                        formula.description,
                        formula.region,
                        item.ingredient.name,
                        item.ingredient.category,
                        item.dose_value,
                        item.dose_unit,
                        item.ingredient.safety_level,
                        formula.created_at.strftime("%Y-%m-%d"),
                    ]
                )

        return response
