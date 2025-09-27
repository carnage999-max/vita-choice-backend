from django.core.mail import send_mail
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

@api_view(["POST"])
def contact_message(request):
    name = request.data.get("name")
    email = request.data.get("email")
    message = request.data.get("message")

    body = f"From: {name} <{email}>\n\n{message}"

    send_mail(
        subject="New Contact Message",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["yourcompany@email.com"],
        fail_silently=False,
    )

    return Response({"success": True, "message": "Message sent!"})
