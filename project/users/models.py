from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string

def generate_customer_id():
    # To avoid circular imports at module level, import User here
    from .models import User
    while True:
        code = ''.join(random.choices(string.digits, k=5))
        cust_id = f"CUST-{code}"
        if not User.objects.filter(customer_id=cust_id).exists():
            return cust_id

class User(AbstractUser):
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True)
    customer_id = models.CharField(max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']
    
    def save(self, *args, **kwargs):
        if not self.customer_id:
            self.customer_id = generate_customer_id()
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.email
