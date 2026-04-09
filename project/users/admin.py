from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'customer_id', 'name', 'order_count', 'date_joined', 'is_active')
    search_fields = ('email', 'customer_id', 'name')
    list_filter = ('is_active', 'date_joined')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('name', 'customer_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2')}),
    )
    readonly_fields = ('customer_id',)

    def order_count(self, obj):
        return obj.orders.count()
    order_count.short_description = 'Orders'
