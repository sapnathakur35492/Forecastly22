from django.db import models


class PricingSettings(models.Model):
    """Singleton model — controls all dynamic pricing parameters from Django Admin."""
    per_country_price = models.PositiveIntegerField(default=20, help_text='Price per country selection ($)')
    global_price = models.PositiveIntegerField(default=20, help_text='Price for Global Market Size ($)')
    segmentation_price = models.PositiveIntegerField(default=99, help_text='Flat fee for 3-Level Segmentation ($)')
    pro_cap = models.PositiveIntegerField(default=199, help_text='Auto-cap when 10+ countries selected ($)')
    pro_cap_threshold = models.PositiveIntegerField(default=10, help_text='Number of countries to trigger Professional cap')
    enterprise_cap = models.PositiveIntegerField(default=299, help_text='Auto-cap for countries + segmentation ($)')
    extra_country_price = models.PositiveIntegerField(default=20, help_text='Per extra custom country beyond cap ($)')
    both_metric_multiplier = models.DecimalField(max_digits=3, decimal_places=1, default=2.0, help_text='Multiplier when Revenue + Volume is selected')
    min_order = models.PositiveIntegerField(default=20, help_text='Minimum order amount ($)')

    # Payment Gateways (Client Keys)
    stripe_public_key = models.CharField(max_length=255, blank=True, help_text="Stripe Publishable Key")
    stripe_secret_key = models.CharField(max_length=255, blank=True, help_text="Stripe Secret Key")
    paypal_client_id = models.CharField(max_length=255, blank=True, help_text="PayPal Client ID")

    class Meta:
        verbose_name = 'Pricing Settings'
        verbose_name_plural = 'Pricing Settings'

    def __str__(self):
        return f"Pricing Config (${self.per_country_price}/country, Cap: ${self.pro_cap}/${self.enterprise_cap})"

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Region(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='countries')
    is_default = models.BooleanField(default=True, help_text='Shown by default in the builder')
    is_rest_of = models.BooleanField(default=False, help_text='Is a "Rest of" aggregate (dashed style)')
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']
        verbose_name_plural = 'Countries'

    def __str__(self):
        return f"{self.name} ({self.region.name})"
