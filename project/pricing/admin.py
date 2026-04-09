from django.contrib import admin
from .models import PricingSettings, Region, Country


class CountryInline(admin.TabularInline):
    model = Country
    extra = 1
    fields = ('name', 'is_default', 'is_rest_of', 'display_order', 'is_active')


@admin.register(PricingSettings)
class PricingSettingsAdmin(admin.ModelAdmin):
    list_display = ('per_country_price', 'global_price', 'segmentation_price', 'pro_cap', 'enterprise_cap')
    fieldsets = (
        ('Per-Unit Pricing', {'fields': ('per_country_price', 'global_price', 'extra_country_price', 'min_order')}),
        ('Segmentation', {'fields': ('segmentation_price',)}),
        ('Auto-Cap Logic', {'fields': ('pro_cap', 'pro_cap_threshold', 'enterprise_cap')}),
        ('Metric Multiplier', {'fields': ('both_metric_multiplier',)}),
    )

    def has_add_permission(self, request):
        return not PricingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order', 'is_active', 'country_count')
    list_editable = ('display_order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [CountryInline]
    ordering = ('display_order',)

    def country_count(self, obj):
        return obj.countries.count()
    country_count.short_description = 'Countries'


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'is_default', 'is_rest_of', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    list_filter = ('region', 'is_default', 'is_rest_of', 'is_active')
    search_fields = ('name',)
    ordering = ('region__display_order', 'display_order')
