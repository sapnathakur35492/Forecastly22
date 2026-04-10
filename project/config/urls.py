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

admin.site.site_header = "Estimately.io Admin"
admin.site.site_title = "Estimately.io Admin"
admin.site.index_title = "Welcome to Estimately.io Dashboard"

from django.http import HttpResponse
import os

def serve_static_root_file(filename, content_type):
    file_path = os.path.join(settings.BASE_DIR, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return HttpResponse(content, content_type=content_type)

def robots_txt(request):
    return serve_static_root_file('robots.txt', 'text/plain')

def sitemap_xml(request):
    return serve_static_root_file('sitemap.xml', 'application/xml')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', robots_txt),
    path('sitemap.xml', sitemap_xml),
    
    # Direct Routes for Separate Pages (SEO-friendly)
    path('', TemplateView.as_view(template_name="index.html"), name='home'),
    path('how-it-works/', TemplateView.as_view(template_name='how-it-works.html')),
    path('behind-the-numbers/', TemplateView.as_view(template_name='behind-the-numbers.html')),
    path('pricing/', TemplateView.as_view(template_name='pricing.html')),
    path('faq/', TemplateView.as_view(template_name='faq.html')),
    path('builder/', TemplateView.as_view(template_name='builder.html'), name='builder'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    
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
