from django.contrib import admin
from .models import SiteSettings, TrustBadge, HowItWorks, Feature, UseCase, FAQ, PricingExample, NavLink, Blog


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'tagline')
    fieldsets = (
        ('Branding', {'fields': ('site_name', 'tagline', 'footer_text', 'support_email', 'support_phone', 'support_chat_hours')}),
        ('Hero Section', {'fields': ('hero_badge_text', 'hero_title', 'hero_subtitle', 'hero_search_placeholder', 'hero_hint_text')}),
        ('Dark CTA Section', {'fields': ('dark_cta_title', 'dark_cta_text', 'dark_cta_button_text', 'dark_cta_note')}),
        ('Excel Preview', {'fields': ('excel_preview_title',)}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TrustBadge)
class TrustBadgeAdmin(admin.ModelAdmin):
    list_display = ('icon', 'label', 'sublabel', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order',)


@admin.register(HowItWorks)
class HowItWorksAdmin(admin.ModelAdmin):
    list_display = ('step_number', 'title', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order',)


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('icon', 'title', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order',)


@admin.register(UseCase)
class UseCaseAdmin(admin.ModelAdmin):
    list_display = ('icon', 'title', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order',)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    list_filter = ('is_active',)
    ordering = ('display_order',)


@admin.register(PricingExample)
class PricingExampleAdmin(admin.ModelAdmin):
    list_display = ('scenario', 'price', 'calculation', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order',)


@admin.register(NavLink)
class NavLinkAdmin(admin.ModelAdmin):
    list_display = ('label', 'scroll_target', 'url', 'is_cta', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active', 'is_cta')
    ordering = ('display_order',)


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('blog_title', 'slug', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('blog_title', 'blog_content', 'meta_title', 'meta_keywords', 'slug')
    prepopulated_fields = {'slug': ('blog_title',)}
    
    fieldsets = (
        ('Content', {
            'fields': ('blog_title', 'slug', 'blog_content')
        }),
        ('SEO Metadata', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'description': 'Fields used for Search Engine Optimization.',
        }),
        ('Publishing & Sorting', {
            'fields': ('is_published',),
        }),
    )
