from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Report, ReportDownloadLog


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'market_name', 'created_at', 'download_count', 'open_file')
    search_fields = ('report_id', 'market_name')
    list_filter = ('created_at',)
    readonly_fields = ('report_id', 'created_at')
    ordering = ('-created_at',)

    def download_count(self, obj):
        return obj.download_logs.count()
    download_count.short_description = 'Downloads'

    def open_file(self, obj):
        if not obj.file_path:
            return '-'
        return format_html('<a href="{}" target="_blank">Open File</a>', obj.file_path.url)
    open_file.short_description = 'File'


@admin.register(ReportDownloadLog)
class ReportDownloadLogAdmin(admin.ModelAdmin):
    list_display = ('report', 'order_link', 'email', 'plan_type', 'is_demo', 'ip_address', 'created_at')
    list_filter = ('is_demo', 'plan_type', 'created_at')
    search_fields = ('report__report_id', 'report__market_name', 'order__order_id', 'email', 'ip_address')
    ordering = ('-created_at',)
    readonly_fields = ('report', 'order', 'email', 'plan_type', 'is_demo', 'ip_address', 'user_agent', 'created_at')

    def order_link(self, obj):
        if not obj.order_id:
            return '-'
        url = reverse('admin:orders_order_change', args=[obj.order.pk])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_id)
    order_link.short_description = 'Order'
