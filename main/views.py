from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .models import ContactMessage
from .models import Product
from .serializers import ProductSerializer
from .email import send_contact_email
from django.core.mail import send_mail
from django.conf import settings


PRODUCT_CACHE_KEY = "product_list_cache"


class ProductViewset(ModelViewSet):
    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = ProductSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        # Try to get the cached response
        cached_data = cache.get(PRODUCT_CACHE_KEY)
        if cached_data is not None:
            print("Cache hit: Returning cached data")
            return Response(cached_data)

        # If not in cache, generate the response
        print("Cache miss: Generating new data")
        response = super().list(request, *args, **kwargs)
        cache.set(PRODUCT_CACHE_KEY, response.data, timeout=60 * 60 * 24)  # 24 hours
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        cache.delete(PRODUCT_CACHE_KEY)  # Clear cache when new product is added
        print("View: Clearing cache on create")
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        cache.delete(PRODUCT_CACHE_KEY)  # Clear cache when product is updated
        print("View: Clearing cache on update")
        return response

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        cache.delete(PRODUCT_CACHE_KEY)  # Clear cache when product is deleted
        print("View: Clearing cache on delete")
        return response


@api_view(["POST"])
@permission_classes([AllowAny])
def contact(request):
    name = request.data.get("name")
    email = request.data.get("email")
    subject = request.data.get("subject", "")
    message = request.data.get("message", "")
    phone_number = request.data.get("phone_number")
    inquiry_type = request.data.get("inquiry_type")
    contact = ContactMessage.objects.create(
        name=name,
        email=email,
        subject=subject,
        message=message,
        phone_number=phone_number,
        inquiry_type=inquiry_type,
    )
    send_contact_email(contact_message=contact)
    return Response({"status": "Message received"}, status=201)
