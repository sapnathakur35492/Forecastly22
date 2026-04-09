from django.db import models
from django.conf import settings
from reports.models import Report
import random
import string

def generate_order_id():
    from .models import Order
    while True:
        code = ''.join(random.choices(string.digits, k=6))
        ord_id = f"MPI-{code}"
        if not Order.objects.filter(order_id=ord_id).exists():
            return ord_id

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
    )
    PAYMENT_CHOICES = (
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    )
    
    order_id = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='stripe', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_email_sent = models.BooleanField(default=False)
    
    # Report Config Fields
    base_year = models.IntegerField(default=2024)
    forecast_year = models.IntegerField(default=2033)
    metric = models.CharField(max_length=50, default='Revenue (USD Million)')
    currency = models.CharField(max_length=10, default='USD')
    has_segmentation = models.BooleanField(default=False)
    has_global = models.BooleanField(default=False)
    countries_list = models.TextField(blank=True, help_text="Comma separated list of countries")

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = generate_order_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} ({self.status})"
