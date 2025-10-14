from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import LoginView, RegisterView, LogoutView, UserProfileView, get_users
from .password_reset_view import ChangePasswordView

urlpatterns = [
    # Register
    path("register/", RegisterView.as_view(), name="register"),
    # Login (get tokens)
    path("login/", LoginView.as_view(), name="token_obtain_pair"),
    # Refresh access token
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Logout
    path("logout/", LogoutView.as_view(), name="logout"),
    # User profile
    path("me/", UserProfileView.as_view(), name="user_profile"),
    # Change password
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    # Get all users
    path("users/", get_users, name="get_users"),
]
