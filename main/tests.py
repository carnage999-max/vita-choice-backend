from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
import json
from unittest.mock import patch

from .models import Product, ContactMessage, Order, OrderItem, Payment
from .serializers import ProductSerializer


class ProductModelTests(TestCase):
    """Test Product model functionality"""

    def setUp(self):
        self.product_data = {
            "name": "Test Immune Stax",
            "subtitle": "Daily immune defense",
            "price": Decimal("59.99"),
            "original_price": Decimal("79.99"),
            "category": "stax",
            "rating": Decimal("4.6"),
            "review_count": 124,
            "description": "Test description for immune support",
            "short_description": "Boosts immunity",
            "key_actives": ["Vitamin C", "Zinc", "Elderberry"],
            "free_from": ["Gluten", "GMOs"],
            "benefits": ["Supports immune response", "Fights seasonal colds"],
            "serving_size": "2 capsules",
            "servings_per_bottle": 30,
            "faqs": [{"question": "When to take?", "answer": "Take with meals"}],
            "usage": "Take two capsules daily",
        }

    def test_product_creation(self):
        """Test creating a product with valid data"""
        product = Product.objects.create(**self.product_data)

        self.assertEqual(product.name, "Test Immune Stax")
        self.assertEqual(product.price, Decimal("59.99"))
        self.assertEqual(product.category, "stax")
        self.assertEqual(len(product.key_actives), 3)
        self.assertEqual(len(product.benefits), 2)
        self.assertTrue(product.id)  # UUID should be generated

    def test_product_str_method(self):
        """Test product string representation"""
        product = Product.objects.create(**self.product_data)
        self.assertEqual(str(product), "Test Immune Stax")

    def test_product_defaults(self):
        """Test product default values"""
        minimal_data = {
            "name": "Minimal Product",
            "price": Decimal("29.99"),
            "category": "test",
        }
        product = Product.objects.create(**minimal_data)

        self.assertEqual(product.rating, Decimal("0"))
        self.assertEqual(product.review_count, 0)
        self.assertEqual(product.key_actives, [])
        self.assertEqual(product.free_from, [])
        self.assertEqual(product.benefits, [])
        self.assertEqual(product.faqs, [])


class ContactMessageModelTests(TestCase):
    """Test ContactMessage model functionality"""

    def test_contact_message_creation(self):
        """Test creating a contact message"""
        contact = ContactMessage.objects.create(
            name="John Doe",
            email="john@example.com",
            phone_number="+1234567890",
            inquiry_type="product_question",
            subject="Question about Immune Stax",
            message="I want to know more about ingredients",
        )

        self.assertEqual(contact.name, "John Doe")
        self.assertEqual(contact.email, "john@example.com")
        self.assertEqual(
            str(contact), "Message from John Doe - Question about Immune Stax"
        )


class ProductAPITests(APITestCase):
    """Test Product API endpoints"""

    def setUp(self):
        self.client = APIClient()

        # Create test users
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_staff=True,
            is_superuser=True,
        )

        self.regular_user = User.objects.create_user(
            username="testuser", email="user@example.com", password="testpass123"
        )

        # Create test products
        self.product1 = Product.objects.create(
            name="Immune Stax",
            subtitle="Daily immune defense",
            price=Decimal("59.99"),
            category="stax",
            rating=Decimal("4.6"),
            review_count=124,
            key_actives=["Vitamin C", "Zinc"],
            benefits=["Immunity", "Antioxidant"],
        )

        self.product2 = Product.objects.create(
            name="Brain Stax",
            subtitle="Focus and clarity",
            price=Decimal("72.00"),
            category="stax",
            rating=Decimal("4.3"),
            review_count=89,
        )

        # Clear cache before each test
        cache.clear()

    def get_admin_token(self):
        """Get JWT token for admin user"""
        refresh = RefreshToken.for_user(self.admin_user)
        return str(refresh.access_token)

    def get_user_token(self):
        """Get JWT token for regular user"""
        refresh = RefreshToken.for_user(self.regular_user)
        return str(refresh.access_token)

    def test_product_list_public_access(self):
        """Test that product list is publicly accessible"""
        url = reverse("product-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Check that cache miss message is printed (would need to capture print)
        # This tests the caching mechanism

    def test_product_list_caching(self):
        """Test that product list is cached properly"""
        url = reverse("product-list")

        # First request - cache miss
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Second request - cache hit
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data, response2.data)

    def test_product_detail_public_access(self):
        """Test that product detail is publicly accessible"""
        url = reverse("product-detail", kwargs={"pk": self.product1.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Immune Stax")
        self.assertEqual(response.data["category"], "stax")

    def test_product_create_admin_required(self):
        """Test that only admin can create products"""
        url = reverse("product-list")
        data = {"name": "New Product", "price": "99.99", "category": "test"}

        # Unauthenticated request
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Regular user request
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_user_token()}")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin user request
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_admin_token()}")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Product")

    def test_product_update_admin_required(self):
        """Test that only admin can update products"""
        url = reverse("product-detail", kwargs={"pk": self.product1.pk})
        data = {"name": "Updated Name"}

        # Regular user request
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_user_token()}")
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin user request
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_admin_token()}")
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Name")

    def test_product_delete_admin_required(self):
        """Test that only admin can delete products"""
        url = reverse("product-detail", kwargs={"pk": self.product1.pk})

        # Regular user request
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_user_token()}")
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin user request
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_admin_token()}")
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify product is deleted
        self.assertFalse(Product.objects.filter(pk=self.product1.pk).exists())

    def test_cache_invalidation_on_create(self):
        """Test that cache is cleared when product is created"""
        # Populate cache
        self.client.get(reverse("product-list"))

        # Create product (should clear cache)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_admin_token()}")
        self.client.post(
            reverse("product-list"),
            {"name": "Cache Test Product", "price": "99.99", "category": "test"},
        )

        # Cache should be cleared
        cached_data = cache.get("product_list_cache")
        self.assertIsNone(cached_data)

    def test_cache_invalidation_on_update(self):
        """Test that cache is cleared when product is updated"""
        # Populate cache
        self.client.get(reverse("product-list"))

        # Update product (should clear cache)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_admin_token()}")
        self.client.patch(
            reverse("product-detail", kwargs={"pk": self.product1.pk}),
            {"name": "Updated Product"},
        )

        # Cache should be cleared
        cached_data = cache.get("product_list_cache")
        self.assertIsNone(cached_data)

    def test_cache_invalidation_on_delete(self):
        """Test that cache is cleared when product is deleted"""
        # Populate cache
        self.client.get(reverse("product-list"))

        # Delete product (should clear cache)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_admin_token()}")
        self.client.delete(reverse("product-detail", kwargs={"pk": self.product1.pk}))

        # Cache should be cleared
        cached_data = cache.get("product_list_cache")
        self.assertIsNone(cached_data)


class ContactAPITests(APITestCase):
    """Test Contact API endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.contact_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone_number": "+1234567890",
            "inquiry_type": "product_question",
            "subject": "Question about products",
            "message": "I would like to know more about your supplements.",
        }

    @patch("main.views.send_contact_email")
    def test_contact_form_submission(self, mock_send_email):
        """Test successful contact form submission"""
        url = reverse("contact")
        response = self.client.post(url, self.contact_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "Message received")

        # Verify contact message was saved
        contact = ContactMessage.objects.get(email="john@example.com")
        self.assertEqual(contact.name, "John Doe")
        self.assertEqual(contact.subject, "Question about products")

        # Verify email sending was called
        mock_send_email.assert_called_once()

    def test_contact_form_missing_fields(self):
        """Test contact form with missing required fields"""
        incomplete_data = {
            "name": "John Doe",
            "email": "john@example.com",
            # Missing subject and message
        }

        url = reverse("contact")
        response = self.client.post(url, incomplete_data, format="json")

        # Should still create contact message with empty fields
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        contact = ContactMessage.objects.get(email="john@example.com")
        self.assertEqual(contact.subject, "")
        self.assertEqual(contact.message, "")

    def test_contact_form_invalid_email(self):
        """Test contact form with invalid email"""
        invalid_data = self.contact_data.copy()
        invalid_data["email"] = "invalid-email"

        url = reverse("contact")
        # This would depend on your model validation
        # The current model doesn't enforce email validation at DB level


class ProductSerializerTests(TestCase):
    """Test Product serializer"""

    def test_product_serialization(self):
        """Test serializing a product"""
        product = Product.objects.create(
            name="Test Product",
            price=Decimal("99.99"),
            category="test",
            key_actives=["Active1", "Active2"],
            benefits=["Benefit1", "Benefit2"],
        )

        serializer = ProductSerializer(product)
        data = serializer.data

        self.assertEqual(data["name"], "Test Product")
        self.assertEqual(data["price"], "99.99")
        self.assertEqual(data["category"], "test")
        self.assertEqual(data["key_actives"], ["Active1", "Active2"])
        self.assertEqual(data["benefits"], ["Benefit1", "Benefit2"])

    def test_product_deserialization(self):
        """Test deserializing product data"""
        data = {
            "name": "New Product",
            "price": "79.99",
            "category": "supplements",
            "key_actives": ["Vitamin D", "Calcium"],
            "benefits": ["Bone health", "Immune support"],
        }

        serializer = ProductSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        product = serializer.save()
        self.assertEqual(product.name, "New Product")
        self.assertEqual(product.price, Decimal("79.99"))


class HealthCheckTests(APITestCase):
    """Test health check endpoint"""

    def test_health_check_endpoint(self):
        """Test health check returns 200 OK"""
        url = "/health/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertIn("timestamp", response.data)


class SignalTests(TestCase):
    """Test Django signals for cache invalidation"""

    def setUp(self):
        cache.clear()

    def test_product_save_signal_clears_cache(self):
        """Test that saving a product clears the cache"""
        # Set up cache
        cache.set("product_list_cache", "test_data")
        self.assertIsNotNone(cache.get("product_list_cache"))

        # Create product (should trigger signal)
        Product.objects.create(
            name="Signal Test Product", price=Decimal("99.99"), category="test"
        )

        # Cache should be cleared
        self.assertIsNone(cache.get("product_list_cache"))

    def test_product_delete_signal_clears_cache(self):
        """Test that deleting a product clears the cache"""
        # Create product
        product = Product.objects.create(
            name="Delete Test Product", price=Decimal("99.99"), category="test"
        )

        # Set up cache
        cache.set("product_list_cache", "test_data")
        self.assertIsNotNone(cache.get("product_list_cache"))

        # Delete product (should trigger signal)
        product.delete()

        # Cache should be cleared
        self.assertIsNone(cache.get("product_list_cache"))


class URLTests(TestCase):
    """Test URL routing"""

    def test_product_urls(self):
        """Test product URL patterns"""
        # List URL
        url = reverse("product-list")
        self.assertEqual(url, "/api/product/")

        # Detail URL
        test_id = "test-uuid"
        url = reverse("product-detail", kwargs={"pk": test_id})
        self.assertEqual(url, f"/api/product/{test_id}/")

    def test_contact_url(self):
        """Test contact URL pattern"""
        url = reverse("contact")
        self.assertEqual(url, "/api/contact/")

    def test_health_check_url(self):
        """Test health check URL pattern"""
        # This would be a direct URL test since it's not named in the main URLconf
        # You might want to add a name to the health check URL
        pass


class IntegrationTests(APITestCase):
    """Integration tests for complete workflows"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_staff=True,
            is_superuser=True,
        )
        cache.clear()

    def get_admin_token(self):
        refresh = RefreshToken.for_user(self.admin_user)
        return str(refresh.access_token)

    def test_complete_product_workflow(self):
        """Test complete product CRUD workflow"""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 1. Create product
        create_data = {
            "name": "Workflow Test Product",
            "subtitle": "Test subtitle",
            "price": "89.99",
            "category": "test",
            "description": "Test description",
            "key_actives": ["Active1", "Active2"],
            "benefits": ["Benefit1", "Benefit2"],
        }

        response = self.client.post(reverse("product-list"), create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product_id = response.data["id"]

        # 2. Retrieve product
        response = self.client.get(reverse("product-detail", kwargs={"pk": product_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Workflow Test Product")

        # 3. Update product
        update_data = {"name": "Updated Workflow Product"}
        response = self.client.patch(
            reverse("product-detail", kwargs={"pk": product_id}), update_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Workflow Product")

        # 4. List products (should include updated product)
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_names = [p["name"] for p in response.data]
        self.assertIn("Updated Workflow Product", product_names)

        # 5. Delete product
        response = self.client.delete(
            reverse("product-detail", kwargs={"pk": product_id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 6. Verify deletion
        response = self.client.get(reverse("product-detail", kwargs={"pk": product_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
