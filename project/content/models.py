from django.db import models


class SiteSettings(models.Model):
    """Singleton model for global site settings — editable from Django Admin."""
    site_name = models.CharField(max_length=100, default='Forecastly.io')
    tagline = models.CharField(max_length=200, default='Market Intelligence')
    hero_title = models.TextField(default='Analyst-verified <span class="accent">Excel datasheets</span> for any market — starting at $20')
    hero_subtitle = models.TextField(default='13-country breakdowns, 3-level segmentation, and 10-year forecasts — validated by our research analysts and delivered to your inbox within 60 minutes.')
    hero_search_placeholder = models.CharField(max_length=200, default='Enter any market — e.g., Electric Vehicle Battery, AI in Healthcare ...')
    hero_hint_text = models.CharField(max_length=300, default='Try: Renewable Energy Storage, Cybersecurity, Digital Therapeutics, Semiconductor')
    hero_badge_text = models.CharField(max_length=200, default='📊 Market Size Estimates & Forecasts in Excel')
    dark_cta_title = models.CharField(max_length=300, default='Your analyst-verified market report, delivered in 60 minutes.')
    dark_cta_text = models.TextField(default='No RFPs. No 6-week timelines. No $5,000 invoices. Download a free demo Excel right now to see the exact report structure — no payment required.')
    dark_cta_button_text = models.CharField(max_length=100, default='Download Free Demo Excel →')
    dark_cta_note = models.CharField(max_length=300, default='FREE DEMO INSTANTLY · FROM $20/COUNTRY · AUTO-CAPS AT $199/$299 · ANALYST-VERIFIED')
    footer_text = models.CharField(max_length=200, default='© 2026 Forecastly.io')
    excel_preview_title = models.CharField(max_length=200, default='Global Renewable Energy Storage Market, 2025–2033 (USD Million)')
    support_email = models.CharField(max_length=200, default='hello@estimately.io', help_text='Support email displayed on dashboard')
    support_phone = models.CharField(max_length=100, default='+1-970-633-3460', help_text='Support phone number')
    support_chat_hours = models.CharField(max_length=200, default='Mon–Fri, 9AM–6PM EST', help_text='Live chat availability hours')

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class TrustBadge(models.Model):
    icon = models.CharField(max_length=10, help_text='Emoji icon, e.g. 🔬')
    label = models.CharField(max_length=100)
    sublabel = models.CharField(max_length=100, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"{self.icon} {self.label}"


class HowItWorks(models.Model):
    step_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = 'How It Works Step'
        verbose_name_plural = 'How It Works Steps'

    def __str__(self):
        return f"Step {self.step_number}: {self.title}"


class Feature(models.Model):
    icon = models.CharField(max_length=10, help_text='Emoji icon')
    title = models.CharField(max_length=200)
    description = models.TextField()
    tags = models.JSONField(default=list, blank=True, help_text='List of tag strings, e.g. ["TAM","CAGR"]')
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title


class UseCase(models.Model):
    icon = models.CharField(max_length=10, help_text='Emoji icon')
    title = models.CharField(max_length=200)
    description = models.TextField()
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField(max_length=500)
    answer = models.TextField()
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question[:60]


class PricingExample(models.Model):
    scenario = models.CharField(max_length=200)
    price = models.CharField(max_length=20, help_text='e.g. $20, $199')
    calculation = models.CharField(max_length=200, help_text='e.g. 1 country × $20')
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"{self.scenario} → {self.price}"


class NavLink(models.Model):
    label = models.CharField(max_length=100)
    scroll_target = models.CharField(max_length=100, blank=True, help_text='Section ID to scroll to, e.g. how-sec')
    url = models.CharField(max_length=200, blank=True, help_text='External URL (overrides scroll_target)')
    display_order = models.PositiveIntegerField(default=0)
    is_cta = models.BooleanField(default=False, help_text='Styled as primary CTA button')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.label


class Blog(models.Model):
    blog_title = models.CharField(max_length=250)
    blog_content = models.TextField()
    meta_title = models.CharField(max_length=250, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True, help_text='Comma-separated keywords')
    slug = models.SlugField(max_length=260, unique=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blog'
        verbose_name_plural = 'Blogs'

    def __str__(self):
        return self.blog_title
