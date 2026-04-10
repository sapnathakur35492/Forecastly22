from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id', 'user_email', 'report_link', 'amount', 'status',
        'has_segmentation', 'payment_method', 'download_logs_count', 'created_at'
    )
    list_filter = ('status', 'has_segmentation', 'payment_method', 'created_at')
    search_fields = ('order_id', 'user__email', 'report__market_name')
    readonly_fields = ('order_id', 'created_at')
    ordering = ('-created_at',)
    actions = ['mark_paid', 'mark_delivered', 'send_delivery_email']

    def mark_paid(self, request, queryset):
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f'{updated} order(s) marked as paid.')
    mark_paid.short_description = '✅ Mark selected orders as Paid'

    def mark_delivered(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='DELIVERED', delivered_at=timezone.now())
        self.message_user(request, f'{updated} order(s) marked as delivered.')
    mark_delivered.short_description = '📦 Mark selected orders as Delivered'

    def send_delivery_email(self, request, queryset):
        count = 0
        for order in queryset.filter(status='COMPLETED'):
            try:
                send_mail(
                    subject=f'Your Report is Ready — {order.order_id}',
                    message=f'Hello,\n\nYour market report "{order.report.market_name}" (Order: {order.order_id}) is ready.\n\nPlease log in to your Estimately.io dashboard to download it.\n\nBest,\nEstimately.io Team',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@Estimately.io'),
                    recipient_list=[order.user.email],
                    fail_silently=True,
                )
                count += 1
            except Exception:
                pass
        self.message_user(request, f'Delivery email sent for {count} order(s).')
    send_delivery_email.short_description = '📧 Send delivery email to customers'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Customer'

    def report_link(self, obj):
        url = reverse('admin:reports_report_change', args=[obj.report_id])
        return format_html('<a href="{}">{} ({})</a>', url, obj.report.report_id, obj.report.market_name[:40])
    report_link.short_description = 'Report'

    def download_logs_count(self, obj):
        return obj.download_logs.count()
    download_logs_count.short_description = 'Downloads'
