import os
import django
from django.conf import settings
from django.core.mail import send_mail
from dotenv import load_dotenv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

load_dotenv(override=True)

print(f"USER: {settings.EMAIL_HOST_USER}")
print(f"PASSWORD: {settings.EMAIL_HOST_PASSWORD}")
print(f"BACKEND: {settings.EMAIL_BACKEND}")

try:
    res = send_mail(
        'Test Email from Estimately',
        'This is a verification test for the SMTP configuration.',
        settings.DEFAULT_FROM_EMAIL,
        ['sapnathakur35492@gmail.com'],
        fail_silently=False,
    )
    print(f"Result: {res}")
except Exception as e:
    print(f"Error: {e}")
