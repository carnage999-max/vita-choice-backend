from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
import json
from unittest.mock import patch

from .models import Ingredient, Formula, FormulaItem
from .serializers import (
    IngredientListSerializer,
    IngredientDetailSerializer,
    FormulaListSerializer,
    FormulaDetailSerializer,
    FormulaItemSerializer,
    ComplianceResultSerializer,
)


class IngredientModelTests(TestCase):
    """Test Ingredient model functionality"""

    def setUp(self):
        self.ingredient_data = {
            "name": "Vitamin C",
            "category": "Vitamins",
            "source": "Synthetic",
            "safety": "General dietary use",
            "evidence": "Well-established antioxidant properties",
        }

    def test_ingredient_creation(self):
        """Test creating an ingredient"""
        ingredient = Ingredient.objects.create(**self.ingredient_data)

        self.assertEqual(ingredient.name, "Vitamin C")
        self.assertEqual(ingredient.category, "Vitamins")
        self.assertEqual(ingredient.source, "Synthetic")
        self.assertEqual(ingredient.safety, "General dietary use")
        self.assertEqual(ingredient.evidence, "Well-established antioxidant properties")
        self.assertIsNotNone(ingredient.created_at)
        self.assertIsNotNone(ingredient.updated_at)

    def test_ingredient_str_representation(self):
        """Test string representation of ingredient"""
        ingredient = Ingredient.objects.create(**self.ingredient_data)
        self.assertEqual(str(ingredient), "Vitamin C")

    def test_ingredient_unique_name(self):
        """Test that ingredient names must be unique"""
        Ingredient.objects.create(**self.ingredient_data)

        # Try to create another ingredient with same name
        with self.assertRaises(Exception):
            Ingredient.objects.create(**self.ingredient_data)

    def test_safety_level_safe(self):
        """Test safety level classification - SAFE"""
        ingredient = Ingredient.objects.create(
            name="Safe Ingredient", safety="General dietary use - well tolerated"
        )
        self.assertEqual(ingredient.safety_level, "SAFE")

    def test_safety_level_caution(self):
        """Test safety level classification - CAUTION"""
        test_cases = [
            "Use with caution in pregnancy",
            "Topical use only",
            "External application recommended",
            "Processing required before use",
            "Contains alkaloids",
        ]

        for safety_text in test_cases:
            ingredient = Ingredient.objects.create(
                name=f"Caution Ingredient {safety_text[:10]}", safety=safety_text
            )
            self.assertEqual(ingredient.safety_level, "CAUTION")

    def test_safety_level_risk(self):
        """Test safety level classification - RISK"""
        test_cases = [
            "Restricted use only",
            "Controlled substance",
            "High-risk ingredient",
        ]

        for safety_text in test_cases:
            ingredient = Ingredient.objects.create(
                name=f"Risk Ingredient {safety_text[:10]}", safety=safety_text
            )
            self.assertEqual(ingredient.safety_level, "RISK")

    def test_safety_level_unknown(self):
        """Test safety level classification - UNKNOWN"""
        ingredient = Ingredient.objects.create(
            name="Unknown Safety Ingredient", safety="Some other safety information"
        )
        self.assertEqual(ingredient.safety_level, "UNKNOWN")

    def test_safety_color_mapping(self):
        """Test safety color property"""
        ingredient_safe = Ingredient.objects.create(
            name="Safe", safety="General dietary use"
        )
        self.assertEqual(ingredient_safe.safety_color, "#4caf50")

        ingredient_caution = Ingredient.objects.create(
            name="Caution", safety="Use with caution"
        )
        self.assertEqual(ingredient_caution.safety_color, "#ff9800")

        ingredient_risk = Ingredient.objects.create(
            name="Risk", safety="Restricted use"
        )
        self.assertEqual(ingredient_risk.safety_color, "#f44336")

        ingredient_unknown = Ingredient.objects.create(
            name="Unknown", safety="Other info"
        )
        self.assertEqual(ingredient_unknown.safety_color, "#757575")


class FormulaModelTests(TestCase):
    """Test Formula model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.formula_data = {
            "owner": self.user,
            "name": "Test Formula",
            "description": "A test supplement formula",
            "region": "US",
        }

        # Create test ingredients
        self.ingredient_safe = Ingredient.objects.create(
            name="Vitamin C", category="Vitamins", safety="General dietary use"
        )

        self.ingredient_caution = Ingredient.objects.create(
            name="Ginseng Extract",
            category="Herbs",
            safety="Use with caution during pregnancy",
        )

        self.ingredient_risk = Ingredient.objects.create(
            name="Controlled Substance", category="Other", safety="Restricted use only"
        )

    def test_formula_creation(self):
        """Test creating a formula"""
        formula = Formula.objects.create(**self.formula_data)

        self.assertEqual(formula.name, "Test Formula")
        self.assertEqual(formula.description, "A test supplement formula")
        self.assertEqual(formula.region, "US")
        self.assertEqual(formula.owner, self.user)
        self.assertIsNotNone(formula.created_at)
        self.assertIsNotNone(formula.updated_at)

    def test_formula_str_representation(self):
        """Test string representation of formula"""
        formula = Formula.objects.create(**self.formula_data)
        expected = f"Test Formula (testuser)"
        self.assertEqual(str(formula), expected)

    def test_total_weight_calculation(self):
        """Test total weight calculation in mg"""
        formula = Formula.objects.create(**self.formula_data)

        # Add items with different units
        FormulaItem.objects.create(
            formula=formula,
            ingredient=self.ingredient_safe,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        FormulaItem.objects.create(
            formula=formula,
            ingredient=self.ingredient_caution,
            dose_value=Decimal("1"),
            dose_unit="g",
        )

        FormulaItem.objects.create(
            formula=formula,
            ingredient=self.ingredient_risk,
            dose_value=Decimal("100"),
            dose_unit="mcg",
        )

        # 500mg + 1000mg (1g) + 0.1mg (100mcg) = 1500.1mg
        expected_weight = 1500.1
        self.assertEqual(formula.total_weight_mg(), expected_weight)

    def test_ingredient_count(self):
        """Test ingredient count method"""
        formula = Formula.objects.create(**self.formula_data)

        self.assertEqual(formula.ingredient_count(), 0)

        FormulaItem.objects.create(
            formula=formula,
            ingredient=self.ingredient_safe,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        self.assertEqual(formula.ingredient_count(), 1)

        FormulaItem.objects.create(
            formula=formula,
            ingredient=self.ingredient_caution,
            dose_value=Decimal("100"),
            dose_unit="mg",
        )

        self.assertEqual(formula.ingredient_count(), 2)

    def test_check_compliance_safe_formula(self):
        """Test compliance check for safe formula"""
        formula = Formula.objects.create(**self.formula_data)

        FormulaItem.objects.create(
            formula=formula,
            ingredient=self.ingredient_safe,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        result = formula.check_compliance()

        self.assertEqual(result["status"], "APPROVED")
        self.assertTrue(result["can_proceed"])
        self.assertEqual(result["summary"]["safe"], 1)
        self.assertEqual(result["summary"]["caution"], 0)
        self.assertEqual(result["summary"]["risk"], 0)
        self.assertEqual(len(result["issues"]), 0)

    def test_check_compliance_caution_formula(self):
        """Test compliance check for formula with caution ingredients"""
        formula = Formula.objects.create(**self.formula_data)

        FormulaItem.objects.create(
            formula=formula,
            ingredient=self.ingredient_safe,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        FormulaItem.objects.create(
            formula=formula,
            ingredient=self.ingredient_caution,
            dose_value=Decimal("100"),
            dose_unit="mg",
        )

        result = formula.check_compliance()

        self.assertEqual(result["status"], "WARNING")
        self.assertTrue(result["can_proceed"])
        self.assertEqual(result["summary"]["safe"], 1)
        self.assertEqual(result["summary"]["caution"], 1)
        self.assertEqual(result["summary"]["risk"], 0)
        self.assertEqual(len(result["issues"]), 1)

        # Check issue details
        issue = result["issues"][0]
        self.assertEqual(issue["severity"], "CAUTION")
        self.assertEqual(issue["ingredient"], "Ginseng Extract")

    def test_check_compliance_risk_formula(self):
        """Test compliance check for formula with risk ingredients"""
        formula = Formula.objects.create(**self.formula_data)

        FormulaItem.objects.create(
            formula=formula,
            ingredient=self.ingredient_risk,
            dose_value=Decimal("10"),
            dose_unit="mg",
        )

        result = formula.check_compliance()

        self.assertEqual(result["status"], "STOP")
        self.assertFalse(result["can_proceed"])
        self.assertEqual(result["summary"]["safe"], 0)
        self.assertEqual(result["summary"]["caution"], 0)
        self.assertEqual(result["summary"]["risk"], 1)
        self.assertEqual(len(result["issues"]), 1)

        # Check issue details
        issue = result["issues"][0]
        self.assertEqual(issue["severity"], "RISK")
        self.assertEqual(issue["ingredient"], "Controlled Substance")


class FormulaItemModelTests(TestCase):
    """Test FormulaItem model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.formula = Formula.objects.create(
            owner=self.user, name="Test Formula", region="US"
        )

        self.ingredient = Ingredient.objects.create(
            name="Vitamin C", category="Vitamins", safety="General dietary use"
        )

    def test_formula_item_creation(self):
        """Test creating a formula item"""
        item = FormulaItem.objects.create(
            formula=self.formula,
            ingredient=self.ingredient,
            dose_value=Decimal("500"),
            dose_unit="mg",
            notes="Daily vitamin C",
            order=1,
        )

        self.assertEqual(item.formula, self.formula)
        self.assertEqual(item.ingredient, self.ingredient)
        self.assertEqual(item.dose_value, Decimal("500"))
        self.assertEqual(item.dose_unit, "mg")
        self.assertEqual(item.notes, "Daily vitamin C")
        self.assertEqual(item.order, 1)

    def test_formula_item_str_representation(self):
        """Test string representation of formula item"""
        item = FormulaItem.objects.create(
            formula=self.formula,
            ingredient=self.ingredient,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        expected = "Vitamin C: 500mg"
        self.assertEqual(str(item), expected)

    def test_formula_item_unique_constraint(self):
        """Test that same ingredient cannot be added twice to same formula"""
        FormulaItem.objects.create(
            formula=self.formula,
            ingredient=self.ingredient,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        # Try to add same ingredient again
        with self.assertRaises(Exception):
            FormulaItem.objects.create(
                formula=self.formula,
                ingredient=self.ingredient,
                dose_value=Decimal("1000"),
                dose_unit="mg",
            )


class IngredientAPITests(APITestCase):
    """Test Ingredient API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create test ingredients
        self.ingredient1 = Ingredient.objects.create(
            name="Vitamin C",
            category="Vitamins",
            source="Synthetic",
            safety="General dietary use",
            evidence="Antioxidant properties",
        )

        self.ingredient2 = Ingredient.objects.create(
            name="Ginseng Extract",
            category="Herbs",
            source="Plant",
            safety="Use with caution",
            evidence="Traditional use",
        )

        self.ingredient3 = Ingredient.objects.create(
            name="Iron",
            category="Minerals",
            source="Synthetic",
            safety="General dietary use",
            evidence="Essential mineral",
        )

    def test_ingredient_list_unauthenticated(self):
        """Test ingredient list access without authentication"""
        url = reverse("ingredient-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_ingredient_list_authenticated(self):
        """Test ingredient list access with authentication"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        url = reverse("ingredient-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_ingredient_detail(self):
        """Test ingredient detail endpoint"""
        url = reverse("ingredient-detail", kwargs={"pk": self.ingredient1.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Vitamin C")
        self.assertEqual(response.data["category"], "Vitamins")
        self.assertEqual(response.data["safety_level"], "SAFE")
        self.assertIn("evidence", response.data)

    def test_ingredient_search(self):
        """Test ingredient search functionality"""
        url = reverse("ingredient-list")
        response = self.client.get(url, {"search": "vitamin"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Vitamin C")

    def test_ingredient_category_filter(self):
        """Test ingredient category filtering"""
        url = reverse("ingredient-list")
        response = self.client.get(url, {"category": "Vitamins"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["category"], "Vitamins")

    def test_ingredient_source_filter(self):
        """Test ingredient source filtering"""
        url = reverse("ingredient-list")
        response = self.client.get(url, {"source": "Plant"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["source"], "Plant")

    def test_ingredient_exclude_risk_filter(self):
        """Test excluding high-risk ingredients"""
        # Create a high-risk ingredient
        Ingredient.objects.create(name="High Risk", safety="Restricted use only")

        url = reverse("ingredient-list")
        response = self.client.get(url, {"exclude_risk": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should exclude the high-risk ingredient
        ingredient_names = [item["name"] for item in response.data["results"]]
        self.assertNotIn("High Risk", ingredient_names)

    def test_ingredient_categories_endpoint(self):
        """Test categories endpoint"""
        url = reverse("ingredient-categories")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Vitamins", response.data)
        self.assertIn("Herbs", response.data)
        self.assertIn("Minerals", response.data)

    def test_ingredient_sources_endpoint(self):
        """Test sources endpoint"""
        url = reverse("ingredient-sources")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Synthetic", response.data)
        self.assertIn("Plant", response.data)

    def test_ingredient_stats_endpoint(self):
        """Test stats endpoint"""
        url = reverse("ingredient-stats")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total", response.data)
        self.assertIn("by_safety_level", response.data)
        self.assertIn("categories", response.data)

        # Check safety level counts
        safety_counts = response.data["by_safety_level"]
        self.assertIn("safe", safety_counts)
        self.assertIn("caution", safety_counts)
        self.assertIn("risk", safety_counts)


class FormulaAPITests(APITestCase):
    """Test Formula API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="otherpass123"
        )

        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Create test ingredients
        self.ingredient = Ingredient.objects.create(
            name="Vitamin C", category="Vitamins", safety="General dietary use"
        )

        # Create test formula
        self.formula = Formula.objects.create(
            owner=self.user,
            name="Test Formula",
            description="Test description",
            region="US",
        )

        # Create formula by other user
        self.other_formula = Formula.objects.create(
            owner=self.other_user, name="Other Formula", region="US"
        )

    def test_formula_list_requires_authentication(self):
        """Test that formula list requires authentication"""
        self.client.credentials()  # Remove authentication
        url = reverse("formula-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_formula_list_shows_only_user_formulas(self):
        """Test that users only see their own formulas"""
        url = reverse("formula-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Test Formula")

    def test_formula_create(self):
        """Test creating a new formula"""
        url = reverse("formula-list")
        data = {"name": "New Formula", "description": "New description", "region": "EU"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Formula")
        self.assertEqual(response.data["owner_username"], "testuser")

        # Verify in database
        formula = Formula.objects.get(name="New Formula")
        self.assertEqual(formula.owner, self.user)

    def test_formula_detail(self):
        """Test formula detail endpoint"""
        url = reverse("formula-detail", kwargs={"pk": self.formula.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Formula")
        self.assertEqual(response.data["owner_username"], "testuser")
        self.assertIn("items", response.data)

    def test_formula_update(self):
        """Test updating a formula"""
        url = reverse("formula-detail", kwargs={"pk": self.formula.pk})
        data = {
            "name": "Updated Formula",
            "description": "Updated description",
            "region": "CA",
        }

        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Formula")

        # Verify in database
        self.formula.refresh_from_db()
        self.assertEqual(self.formula.name, "Updated Formula")

    def test_formula_delete(self):
        """Test deleting a formula"""
        url = reverse("formula-detail", kwargs={"pk": self.formula.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify deletion
        self.assertFalse(Formula.objects.filter(pk=self.formula.pk).exists())

    def test_formula_access_control(self):
        """Test that users cannot access other users' formulas"""
        url = reverse("formula-detail", kwargs={"pk": self.other_formula.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_ingredient_to_formula(self):
        """Test adding an ingredient to a formula"""
        url = reverse("formula-add-ingredient", kwargs={"pk": self.formula.pk})
        data = {
            "ingredient_id": self.ingredient.id,
            "dose_value": 500,
            "dose_unit": "mg",
            "notes": "Daily vitamin C",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["dose_value"], "500.00")
        self.assertEqual(response.data["dose_unit"], "mg")

        # Verify in database
        item = FormulaItem.objects.get(formula=self.formula, ingredient=self.ingredient)
        self.assertEqual(item.dose_value, Decimal("500"))

    def test_add_duplicate_ingredient_fails(self):
        """Test that adding duplicate ingredient fails"""
        # Add ingredient first time
        FormulaItem.objects.create(
            formula=self.formula,
            ingredient=self.ingredient,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        # Try to add same ingredient again
        url = reverse("formula-add-ingredient", kwargs={"pk": self.formula.pk})
        data = {
            "ingredient_id": self.ingredient.id,
            "dose_value": 1000,
            "dose_unit": "mg",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already exists", response.data["error"])

    def test_remove_ingredient_from_formula(self):
        """Test removing an ingredient from a formula"""
        # Add ingredient first
        item = FormulaItem.objects.create(
            formula=self.formula,
            ingredient=self.ingredient,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        url = reverse(
            "formula-remove-ingredient",
            kwargs={"pk": self.formula.pk, "item_id": item.id},
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify deletion
        self.assertFalse(FormulaItem.objects.filter(id=item.id).exists())

    def test_update_ingredient_in_formula(self):
        """Test updating an ingredient in a formula"""
        # Add ingredient first
        item = FormulaItem.objects.create(
            formula=self.formula,
            ingredient=self.ingredient,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        url = reverse(
            "formula-update-ingredient",
            kwargs={"pk": self.formula.pk, "item_id": item.id},
        )
        data = {"dose_value": 1000, "dose_unit": "mg", "notes": "Updated dosage"}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["dose_value"], "1000.00")
        self.assertEqual(response.data["notes"], "Updated dosage")

        # Verify in database
        item.refresh_from_db()
        self.assertEqual(item.dose_value, Decimal("1000"))

    def test_duplicate_formula(self):
        """Test duplicating a formula"""
        # Add ingredient to original formula
        FormulaItem.objects.create(
            formula=self.formula,
            ingredient=self.ingredient,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        url = reverse("formula-duplicate", kwargs={"pk": self.formula.pk})
        data = {"name": "Duplicated Formula"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Duplicated Formula")
        self.assertEqual(len(response.data["items"]), 1)

        # Verify in database
        new_formula = Formula.objects.get(name="Duplicated Formula")
        self.assertEqual(new_formula.owner, self.user)
        self.assertEqual(new_formula.items.count(), 1)

    def test_check_compliance_empty_formula(self):
        """Test compliance check on empty formula"""
        url = reverse("formula-check-compliance", kwargs={"pk": self.formula.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("no ingredients", response.data["error"])

    def test_check_compliance_with_ingredients(self):
        """Test compliance check with ingredients"""
        # Add ingredient to formula
        FormulaItem.objects.create(
            formula=self.formula,
            ingredient=self.ingredient,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        url = reverse("formula-check-compliance", kwargs={"pk": self.formula.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
        self.assertIn("summary", response.data)
        self.assertIn("issues", response.data)

    def test_compliance_summary(self):
        """Test compliance summary endpoint"""
        # Add ingredient to formula
        FormulaItem.objects.create(
            formula=self.formula,
            ingredient=self.ingredient,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        url = reverse("formula-compliance-summary", kwargs={"pk": self.formula.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
        self.assertIn("summary", response.data)
        self.assertEqual(response.data["status"], "APPROVED")

    def test_export_csv(self):
        """Test CSV export"""
        # Add ingredient to formula
        FormulaItem.objects.create(
            formula=self.formula,
            ingredient=self.ingredient,
            dose_value=Decimal("500"),
            dose_unit="mg",
            notes="Daily vitamin",
        )

        url = reverse("formula-export-csv", kwargs={"pk": self.formula.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_export_csv_empty_formula(self):
        """Test CSV export with empty formula"""
        url = reverse("formula-export-csv", kwargs={"pk": self.formula.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("no ingredients", response.data["error"])


class SerializerTests(TestCase):
    """Test serializer functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.ingredient = Ingredient.objects.create(
            name="Vitamin C",
            category="Vitamins",
            source="Synthetic",
            safety="General dietary use",
            evidence="Antioxidant properties",
        )

        self.formula = Formula.objects.create(
            owner=self.user, name="Test Formula", region="US"
        )

    def test_ingredient_list_serializer(self):
        """Test IngredientListSerializer"""
        serializer = IngredientListSerializer(self.ingredient)
        data = serializer.data

        self.assertEqual(data["name"], "Vitamin C")
        self.assertEqual(data["category"], "Vitamins")
        self.assertEqual(data["safety_level"], "SAFE")
        self.assertEqual(data["safety_color"], "#4caf50")
        # Evidence should not be in list view
        self.assertNotIn("evidence", data)

    def test_ingredient_detail_serializer(self):
        """Test IngredientDetailSerializer"""
        serializer = IngredientDetailSerializer(self.ingredient)
        data = serializer.data

        self.assertEqual(data["name"], "Vitamin C")
        self.assertEqual(data["category"], "Vitamins")
        self.assertEqual(data["safety_level"], "SAFE")
        self.assertIn("evidence", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_formula_item_serializer(self):
        """Test FormulaItemSerializer"""
        item = FormulaItem.objects.create(
            formula=self.formula,
            ingredient=self.ingredient,
            dose_value=Decimal("500"),
            dose_unit="mg",
            notes="Daily vitamin",
        )

        serializer = FormulaItemSerializer(item)
        data = serializer.data

        self.assertEqual(data["dose_value"], "500.00")
        self.assertEqual(data["dose_unit"], "mg")
        self.assertEqual(data["notes"], "Daily vitamin")
        self.assertEqual(data["ingredient_name"], "Vitamin C")
        self.assertEqual(data["safety_level"], "SAFE")

    def test_formula_item_serializer_validation(self):
        """Test FormulaItemSerializer validation"""
        # Test with invalid ingredient ID
        data = {
            "ingredient_id": 99999,  # Non-existent
            "dose_value": 500,
            "dose_unit": "mg",
        }

        serializer = FormulaItemSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("ingredient_id", serializer.errors)

    def test_formula_list_serializer(self):
        """Test FormulaListSerializer"""
        serializer = FormulaListSerializer(self.formula)
        data = serializer.data

        self.assertEqual(data["name"], "Test Formula")
        self.assertEqual(data["owner_username"], "testuser")
        self.assertEqual(data["item_count"], 0)
        self.assertIn("compliance_status", data)
        # Items should not be in list view
        self.assertNotIn("items", data)

    def test_formula_detail_serializer(self):
        """Test FormulaDetailSerializer"""
        # Add an item to the formula
        FormulaItem.objects.create(
            formula=self.formula,
            ingredient=self.ingredient,
            dose_value=Decimal("500"),
            dose_unit="mg",
        )

        serializer = FormulaDetailSerializer(self.formula)
        data = serializer.data

        self.assertEqual(data["name"], "Test Formula")
        self.assertEqual(data["owner_username"], "testuser")
        self.assertEqual(data["item_count"], 1)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        self.assertIn("total_weight", data)


class URLTests(TestCase):
    """Test URL routing for ingredients app"""

    def test_ingredient_urls(self):
        """Test ingredient URL patterns"""
        # Ingredient list
        url = reverse("ingredient-list")
        self.assertEqual(url, "/api/ingredients/")

        # Ingredient detail
        url = reverse("ingredient-detail", kwargs={"pk": 1})
        self.assertEqual(url, "/api/ingredients/1/")

        # Ingredient categories
        url = reverse("ingredient-categories")
        self.assertEqual(url, "/api/ingredients/categories/")

        # Ingredient sources
        url = reverse("ingredient-sources")
        self.assertEqual(url, "/api/ingredients/sources/")

        # Ingredient stats
        url = reverse("ingredient-stats")
        self.assertEqual(url, "/api/ingredients/stats/")

    def test_formula_urls(self):
        """Test formula URL patterns"""
        # Formula list
        url = reverse("formula-list")
        self.assertEqual(url, "/api/formulas/")

        # Formula detail
        url = reverse("formula-detail", kwargs={"pk": 1})
        self.assertEqual(url, "/api/formulas/1/")

        # Add ingredient
        url = reverse("formula-add-ingredient", kwargs={"pk": 1})
        self.assertEqual(url, "/api/formulas/1/add_ingredient/")

        # Remove ingredient
        url = reverse("formula-remove-ingredient", kwargs={"pk": 1, "item_id": 2})
        self.assertEqual(url, "/api/formulas/1/remove_ingredient/2/")

        # Update ingredient
        url = reverse("formula-update-ingredient", kwargs={"pk": 1, "item_id": 2})
        self.assertEqual(url, "/api/formulas/1/update_ingredient/2/")

        # Duplicate formula
        url = reverse("formula-duplicate", kwargs={"pk": 1})
        self.assertEqual(url, "/api/formulas/1/duplicate/")

        # Check compliance
        url = reverse("formula-check-compliance", kwargs={"pk": 1})
        self.assertEqual(url, "/api/formulas/1/check_compliance/")

        # Compliance summary
        url = reverse("formula-compliance-summary", kwargs={"pk": 1})
        self.assertEqual(url, "/api/formulas/1/compliance_summary/")

        # Export CSV
        url = reverse("formula-export-csv", kwargs={"pk": 1})
        self.assertEqual(url, "/api/formulas/1/export_csv/")


class IntegrationTests(APITestCase):
    """Integration tests for complete workflows"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Authenticate
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        # Create test ingredients
        self.vitamin_c = Ingredient.objects.create(
            name="Vitamin C", category="Vitamins", safety="General dietary use"
        )

        self.ginseng = Ingredient.objects.create(
            name="Ginseng", category="Herbs", safety="Use with caution during pregnancy"
        )

        self.restricted = Ingredient.objects.create(
            name="Restricted Item", category="Other", safety="Restricted use only"
        )

    def test_complete_formula_workflow(self):
        """Test complete formula creation and management workflow"""

        # 1. Create formula
        create_url = reverse("formula-list")
        formula_data = {
            "name": "My Supplement",
            "description": "A complete supplement formula",
            "region": "US",
        }

        response = self.client.post(create_url, formula_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        formula_id = response.data["id"]

        # 2. Add safe ingredient
        add_url = reverse("formula-add-ingredient", kwargs={"pk": formula_id})
        ingredient_data = {
            "ingredient_id": self.vitamin_c.id,
            "dose_value": 500,
            "dose_unit": "mg",
            "notes": "Daily vitamin C",
        }

        response = self.client.post(add_url, ingredient_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item_id = response.data["id"]

        # 3. Check compliance (should be APPROVED)
        compliance_url = reverse("formula-check-compliance", kwargs={"pk": formula_id})
        response = self.client.post(compliance_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "APPROVED")

        # 4. Add caution ingredient
        caution_data = {
            "ingredient_id": self.ginseng.id,
            "dose_value": 100,
            "dose_unit": "mg",
            "notes": "Herbal extract",
        }

        response = self.client.post(add_url, caution_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 5. Check compliance again (should be WARNING)
        response = self.client.post(compliance_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "WARNING")
        self.assertEqual(len(response.data["issues"]), 1)

        # 6. Update ingredient dosage
        update_url = reverse(
            "formula-update-ingredient", kwargs={"pk": formula_id, "item_id": item_id}
        )
        update_data = {"dose_value": 1000, "notes": "Increased dosage"}

        response = self.client.patch(update_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["dose_value"], "1000.00")

        # 7. Export formula as CSV
        export_url = reverse("formula-export-csv", kwargs={"pk": formula_id})
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")

        # 8. Duplicate formula
        duplicate_url = reverse("formula-duplicate", kwargs={"pk": formula_id})
        duplicate_data = {"name": "My Supplement v2"}

        response = self.client.post(duplicate_url, duplicate_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "My Supplement v2")
        self.assertEqual(len(response.data["items"]), 2)

        # 9. Verify formula list shows both formulas
        list_url = reverse("formula-list")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_high_risk_compliance_workflow(self):
        """Test workflow with high-risk ingredients"""

        # 1. Create formula
        create_url = reverse("formula-list")
        formula_data = {"name": "Risky Formula", "region": "US"}

        response = self.client.post(create_url, formula_data)
        formula_id = response.data["id"]

        # 2. Add restricted ingredient
        add_url = reverse("formula-add-ingredient", kwargs={"pk": formula_id})
        ingredient_data = {
            "ingredient_id": self.restricted.id,
            "dose_value": 10,
            "dose_unit": "mg",
        }

        response = self.client.post(add_url, ingredient_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 3. Check compliance (should be STOP)
        compliance_url = reverse("formula-check-compliance", kwargs={"pk": formula_id})
        response = self.client.post(compliance_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "STOP")
        self.assertFalse(response.data["can_proceed"])
        self.assertEqual(response.data["summary"]["risk"], 1)

    def test_ingredient_search_and_filtering_workflow(self):
        """Test ingredient discovery workflow"""

        # 1. Search for vitamins
        search_url = reverse("ingredient-list")
        response = self.client.get(search_url, {"search": "vitamin"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. Filter by category
        response = self.client.get(search_url, {"category": "Vitamins"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vitamin_ingredients = response.data["results"]

        # 3. Exclude high-risk ingredients
        response = self.client.get(search_url, {"exclude_risk": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        safe_ingredients = response.data["results"]

        # Should have fewer ingredients when excluding risk
        all_response = self.client.get(search_url)
        self.assertLessEqual(len(safe_ingredients), len(all_response.data["results"]))

        # 4. Get categories and sources
        categories_url = reverse("ingredient-categories")
        response = self.client.get(categories_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        sources_url = reverse("ingredient-sources")
        response = self.client.get(sources_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 5. Get stats
        stats_url = reverse("ingredient-stats")
        response = self.client.get(stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("by_safety_level", response.data)
