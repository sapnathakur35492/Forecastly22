from django.contrib import admin
from django.urls import path
from ai_engine.views import generate_segmentation
from reports.views import download_excel, update_report
from orders.views import create_order, mark_paid, get_orders
from payments.views import payment_webhook, create_stripe_session, create_paypal_order, capture_paypal_order, paypal_config
from users.views import send_otp, verify_otp
from content.views import site_config, blog_list_page, blog_detail_page
from pricing.views import pricing_config, regions_list
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Forecastly.io Admin"
admin.site.site_title = "Forecastly.io Admin"
admin.site.index_title = "Welcome to Forecastly.io Dashboard"

from django.http import HttpResponse
from django.contrib.sitemaps.views import sitemap
from .sitemaps import sitemaps

def robots_txt(request):
    host = request.get_host()
    protocol = "https" if request.is_secure() else "http"
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /api/",
        "Allow: /",
        f"Sitemap: {protocol}://{host}/sitemap.xml"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', robots_txt),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('', TemplateView.as_view(template_name="index.html"), name='home'),
    path('blog/', blog_list_page, name='blog-list'),
    path('blog/<slug:slug>/', blog_detail_page, name='blog-detail'),

    # Content & Config APIs (dynamic from DB)
    path('api/site-config/', site_config),
    path('api/regions/', regions_list),
    path('api/pricing-config/', pricing_config),

    # AI Segmentation
    path('api/generate/', generate_segmentation),

    # Reports
    path('api/report/update/<str:report_id>/', update_report),
    path('api/download/<str:report_id>/<str:plan_type>/', download_excel),

    # Orders
    path('api/order/', create_order),
    path('api/order/paid/', mark_paid),
    path('api/order/list/', get_orders),

    # Payments
    path('api/payment/webhook/', payment_webhook),
    path('api/payment/stripe/session/', create_stripe_session),
    path('api/payment/paypal/order/', create_paypal_order),
    path('api/payment/paypal/capture/', capture_paypal_order),
    path('api/payment/paypal/config/', paypal_config),

    # Auth
    path('api/send-otp/', send_otp),
    path('api/verify-otp/', verify_otp),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
