from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ContactMessage
from .models import Product
from .serializers import ProductSerializer
from .email import send_contact_email
from django.core.mail import send_mail
from django.conf import settings


class ProductViewset(ModelViewSet):
    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]


@api_view(["POST"])
def contact(request):
    name = request.data.get("name")
    email = request.data.get("email")
    subject = request.data.get("subject")
    message = request.data.get("message")
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
