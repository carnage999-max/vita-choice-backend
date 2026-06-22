import requests
from django.conf import settings
from .models import ContactMessage


def send_contact_email(contact_message):
    subject = f"New Contact Message: {contact_message.subject}"
    message = f"""
    You have received a new message from {contact_message.name} ({contact_message.email}).
    
    Inquiry Type: {contact_message.inquiry_type}
    Phone Number: {contact_message.phone_number}
    
    Message:
    {contact_message.message}
    """
    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [settings.CONTACT_EMAIL_RECIPIENT],
            "reply_to": contact_message.email,
            "subject": subject,
            "text": message,
        },
        timeout=30,
    )
    response.raise_for_status()
