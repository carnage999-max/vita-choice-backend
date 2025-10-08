from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import json
from datetime import datetime, timedelta

from .serializers import UserSerializer, RegisterSerializer, ChangePasswordSerializer


User = get_user_model()


class UserModelTests(TestCase):
    """Test User model functionality"""

    def setUp(self):
        self.user_data = {
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_user_creation(self):
        """Test creating a user"""
        user = User.objects.create_user(**self.user_data)

        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_superuser_creation(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class RegisterViewTests(APITestCase):
    """Test user registration"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("register")
        self.valid_data = {
            "email": "newuser@example.com",
            "password": "NewPass123!",
            "password2": "NewPass123!",
            "first_name": "New",
            "last_name": "User",
        }

    def test_successful_registration(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.valid_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

        # Verify user was created
        user = User.objects.get(email="newuser@example.com")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.last_name, "User")

    def test_registration_password_mismatch(self):
        """Test registration with password mismatch"""
        invalid_data = self.valid_data.copy()
        invalid_data["password2"] = "DifferentPass123!"

        response = self.client.post(self.register_url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create user with email
        User.objects.create_user(email="duplicate@example.com", password="pass123")

        # Try to register with same email
        invalid_data = self.valid_data.copy()
        invalid_data["email"] = "duplicate@example.com"

        response = self.client.post(self.register_url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registration_weak_password(self):
        """Test registration with weak password"""
        invalid_data = self.valid_data.copy()
        invalid_data["password"] = "123"
        invalid_data["password2"] = "123"

        response = self.client.post(self.register_url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registration_missing_required_fields(self):
        """Test registration with missing required fields"""
        incomplete_data = {
            "password": "TestPass123!",
            "password2": "TestPass123!",
            # Missing email
        }

        response = self.client.post(self.register_url, incomplete_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)


class LoginViewTests(APITestCase):
    """Test user login (JWT token obtain)"""

    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("token_obtain_pair")

        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

    def test_successful_login(self):
        """Test successful login"""
        login_data = {"email": "test@example.com", "password": "testpass123"}

        response = self.client.post(self.login_url, login_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        invalid_data = {"email": "test@example.com", "password": "wrongpassword"}

        response = self.client.post(self.login_url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user"""
        invalid_data = {"email": "nonexistent@example.com", "password": "password123"}

        response = self.client.post(self.login_url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_login_missing_fields(self):
        """Test login with missing fields"""
        incomplete_data = {
            "email": "test@example.com"
            # Missing password
        }

        response = self.client.post(self.login_url, incomplete_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TokenRefreshViewTests(APITestCase):
    """Test JWT token refresh"""

    def setUp(self):
        self.client = APIClient()
        self.refresh_url = reverse("token_refresh")

        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        self.refresh_token = RefreshToken.for_user(self.user)

    def test_successful_token_refresh(self):
        """Test successful token refresh"""
        refresh_data = {"refresh": str(self.refresh_token)}

        response = self.client.post(self.refresh_url, refresh_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_refresh_invalid_token(self):
        """Test token refresh with invalid token"""
        invalid_data = {"refresh": "invalid_token"}

        response = self.client.post(self.refresh_url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_missing_token(self):
        """Test token refresh with missing token"""
        response = self.client.post(self.refresh_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTests(APITestCase):
    """Test user logout"""

    def setUp(self):
        self.client = APIClient()
        self.logout_url = reverse("logout")

        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        self.refresh_token = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh_token.access_token)

    def test_successful_logout(self):
        """Test successful logout"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        logout_data = {"refresh": str(self.refresh_token)}

        response = self.client.post(self.logout_url, logout_data)

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(response.data["message"], "Logout successful")

    def test_logout_without_authentication(self):
        """Test logout without authentication"""
        logout_data = {"refresh": str(self.refresh_token)}

        response = self.client.post(self.logout_url, logout_data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_missing_refresh_token(self):
        """Test logout without refresh token"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        response = self.client.post(self.logout_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_logout_invalid_refresh_token(self):
        """Test logout with invalid refresh token"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        logout_data = {"refresh": "invalid_token"}

        response = self.client.post(self.logout_url, logout_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileViewTests(APITestCase):
    """Test user profile management"""

    def setUp(self):
        self.client = APIClient()
        self.profile_url = reverse("user_profile")

        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_get_user_profile(self):
        """Test retrieving user profile"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["first_name"], "Test")
        self.assertEqual(response.data["last_name"], "User")
        self.assertIn("id", response.data)
        self.assertIn("date_joined", response.data)

    def test_update_user_profile(self):
        """Test updating user profile"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
        }

        response = self.client.put(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Updated")
        self.assertEqual(response.data["last_name"], "Name")
        self.assertEqual(response.data["email"], "updated@example.com")

        # Verify changes in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")
        self.assertEqual(self.user.email, "updated@example.com")

    def test_partial_update_user_profile(self):
        """Test partial update of user profile"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        update_data = {"first_name": "Partially Updated"}

        response = self.client.patch(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Partially Updated")
        self.assertEqual(response.data["last_name"], "User")  # Should remain unchanged

    def test_profile_access_without_authentication(self):
        """Test accessing profile without authentication"""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_update_without_authentication(self):
        """Test updating profile without authentication"""
        update_data = {"first_name": "Should Not Work"}

        response = self.client.put(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangePasswordViewTests(APITestCase):
    """Test password change functionality"""

    def setUp(self):
        self.client = APIClient()
        self.change_password_url = reverse("change_password")

        self.user = User.objects.create_user(
            email="test@example.com", password="oldpass123"
        )

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_successful_password_change(self):
        """Test successful password change"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        change_data = {"old_password": "oldpass123", "new_password": "NewPass456!"}

        response = self.client.post(self.change_password_url, change_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password changed successfully")

        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456!"))
        self.assertFalse(self.user.check_password("oldpass123"))

    def test_password_change_wrong_old_password(self):
        """Test password change with wrong old password"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        change_data = {"old_password": "wrongpass", "new_password": "NewPass456!"}

        response = self.client.post(self.change_password_url, change_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("incorrect", response.data["error"])

    def test_password_change_weak_new_password(self):
        """Test password change with weak new password"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        change_data = {"old_password": "oldpass123", "new_password": "123"}

        response = self.client.post(self.change_password_url, change_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

    def test_password_change_without_authentication(self):
        """Test password change without authentication"""
        change_data = {"old_password": "oldpass123", "new_password": "NewPass456!"}

        response = self.client.post(self.change_password_url, change_data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_change_missing_fields(self):
        """Test password change with missing fields"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        incomplete_data = {
            "old_password": "oldpass123"
            # Missing new_password
        }

        response = self.client.post(self.change_password_url, incomplete_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)


class UserSerializerTests(TestCase):
    """Test User serializers"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_user_serializer(self):
        """Test UserSerializer"""
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["first_name"], "Test")
        self.assertEqual(data["last_name"], "User")
        self.assertIn("id", data)
        self.assertIn("date_joined", data)
        # Password should not be included
        self.assertNotIn("password", data)

    def test_register_serializer_valid_data(self):
        """Test RegisterSerializer with valid data"""
        data = {
            "email": "new@example.com",
            "password": "NewPass123!",
            "password2": "NewPass123!",
            "first_name": "New",
            "last_name": "User",
        }

        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.check_password("NewPass123!"))

    def test_register_serializer_password_mismatch(self):
        """Test RegisterSerializer with password mismatch"""
        data = {
            "email": "new@example.com",
            "password": "NewPass123!",
            "password2": "DifferentPass123!",
            "first_name": "New",
            "last_name": "User",
        }

        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_register_serializer_duplicate_email(self):
        """Test RegisterSerializer with duplicate email"""
        data = {
            "email": "test@example.com",  # Same as existing user
            "password": "NewPass123!",
            "password2": "NewPass123!",
            "first_name": "New",
            "last_name": "User",
        }

        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_change_password_serializer(self):
        """Test ChangePasswordSerializer"""
        data = {"old_password": "oldpass123", "new_password": "NewPass456!"}

        serializer = ChangePasswordSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Test with weak password
        weak_data = {"old_password": "oldpass123", "new_password": "123"}

        serializer = ChangePasswordSerializer(data=weak_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password", serializer.errors)


class AuthenticationIntegrationTests(APITestCase):
    """Integration tests for authentication flow"""

    def setUp(self):
        self.client = APIClient()

    def test_complete_auth_flow(self):
        """Test complete authentication flow: register -> login -> profile -> logout"""

        # 1. Register
        register_data = {
            "email": "flow@example.com",
            "password": "FlowPass123!",
            "password2": "FlowPass123!",
            "first_name": "Flow",
            "last_name": "User",
        }

        response = self.client.post(reverse("register"), register_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Extract tokens from registration
        access_token = response.data["tokens"]["access"]
        refresh_token = response.data["tokens"]["refresh"]

        # 2. Access profile with registration token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(reverse("user_profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "flow@example.com")

        # 3. Login (get new tokens)
        login_data = {"email": "flow@example.com", "password": "FlowPass123!"}

        response = self.client.post(reverse("token_obtain_pair"), login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_access_token = response.data["access"]
        new_refresh_token = response.data["refresh"]

        # 4. Use new access token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access_token}")
        response = self.client.get(reverse("user_profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 5. Refresh token
        refresh_data = {"refresh": new_refresh_token}
        response = self.client.post(reverse("token_refresh"), refresh_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        refreshed_access_token = response.data["access"]

        # 6. Use refreshed token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refreshed_access_token}")
        response = self.client.get(reverse("user_profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 7. Logout
        logout_data = {"refresh": new_refresh_token}
        response = self.client.post(reverse("logout"), logout_data)
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_token_security(self):
        """Test token security measures"""
        # Create user
        user = User.objects.create_user(
            email="security@example.com",
            password="SecurityPass123!",
        )

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Test access with valid token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(reverse("user_profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test access with invalid token
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = self.client.get(reverse("user_profile"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test access without token
        self.client.credentials()
        response = self.client.get(reverse("user_profile"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class URLTests(TestCase):
    """Test URL routing for users app"""

    def test_auth_urls(self):
        """Test authentication URL patterns"""
        # Register URL
        url = reverse("register")
        self.assertEqual(url, "/api/auth/register/")

        # Login URL
        url = reverse("token_obtain_pair")
        self.assertEqual(url, "/api/auth/login/")

        # Refresh URL
        url = reverse("token_refresh")
        self.assertEqual(url, "/api/auth/refresh/")

        # Logout URL
        url = reverse("logout")
        self.assertEqual(url, "/api/auth/logout/")

        # Profile URL
        url = reverse("user_profile")
        self.assertEqual(url, "/api/auth/me/")

        # Change password URL
        url = reverse("change_password")
        self.assertEqual(url, "/api/auth/change-password/")
