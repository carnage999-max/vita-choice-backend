from django.core.mail import send_mail
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
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        ['ezekielokebule@proton.me'],
        fail_silently=False,
    )