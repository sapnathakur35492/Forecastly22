from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Order
from reports.models import Report
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
import threading

User = get_user_model()


def calculate_price_server(countries_list_str, is_global, has_segmentation, metric_value='revenue'):
    """
    Server-side price calculation — must match frontend logic exactly.
    This is the single source of truth for pricing.
    """
    from pricing.models import PricingSettings
    pricing = PricingSettings.load()

    countries_all = [c.strip() for c in countries_list_str.split(',') if c.strip()]
    default_count = len(countries_all)
    global_count = 1 if is_global else 0
    total_units = default_count + global_count

    # Base: per-country pricing
    raw_default = total_units * pricing.per_country_price

    # Pro cap: if >= threshold countries, cap at pro price
    if total_units >= pricing.pro_cap_threshold:
        capped_default = min(raw_default, pricing.pro_cap)
    else:
        capped_default = raw_default

    # Segmentation flat fee
    seg_price = pricing.segmentation_price if has_segmentation else 0

    # Enterprise cap: countries + segmentation capped
    subtotal = capped_default + seg_price
    capped_sub = min(subtotal, pricing.enterprise_cap)

    # Both metric multiplier
    if metric_value == 'both':
        capped_sub = int(capped_sub * float(pricing.both_metric_multiplier))

    # Never negative
    calculated_total = max(capped_sub, 0)

    return calculated_total


@api_view(['POST'])
@permission_classes([AllowAny])
def create_order(request):
    report_id = request.data.get('reportId')
    email = request.data.get('email')

    # Config Params
    base_year = request.data.get('base_year', 2024)
    forecast_year = request.data.get('forecast_year', 2033)
    metric = request.data.get('metric', 'Revenue (USD Million)')
    currency = request.data.get('currency', 'USD')
    has_segmentation = request.data.get('has_segmentation', False)
    countries_list = request.data.get('countries_list', '')
    is_global = request.data.get('is_global', False)
    payment_method = request.data.get('payment_method', 'stripe')
    frontend_total = request.data.get('total', 0)

    # Validation
    if not all([report_id, email]):
        return Response({"error": "Missing required fields (reportId, email)"}, status=400)

    if not email or '@' not in email or '.' not in email:
        return Response({"error": "Invalid email address"}, status=400)

    # Server-side price verification
    metric_value = request.data.get('metric_value', 'revenue')
    if not metric_value:
        metric_val_lower = str(metric).lower()
        if 'both' in metric_val_lower:
            metric_value = 'both'
        elif 'volume' in metric_val_lower:
            metric_value = 'volume'
        else:
            metric_value = 'revenue'

    calculated_total = calculate_price_server(
        countries_list, is_global, has_segmentation, metric_value
    )

    # Verify frontend total matches backend (allow small tolerance for rounding)
    try:
        ft = float(frontend_total)
    except (TypeError, ValueError):
        ft = 0.0

    if abs(ft - calculated_total) > 1:
        return Response({
            "error": "Price mismatch. Please refresh and try again.",
            "server_price": calculated_total,
            "client_price": ft
        }, status=400)

    # Validate countries list
    if not countries_list and not is_global:
        return Response({"error": "Please select at least one country or Global"}, status=400)

    user, _ = User.objects.get_or_create(email=email, defaults={'username': email})
    report = get_object_or_404(Report, report_id=report_id)

    order = Order.objects.create(
        user=user,
        report=report,
        amount=calculated_total,
        status='PENDING',
        payment_method=payment_method,
        base_year=base_year,
        forecast_year=forecast_year,
        metric=metric,
        currency=currency,
        has_segmentation=has_segmentation,
        has_global=is_global,
        countries_list=countries_list
    )

    return Response({
        "order_id": order.order_id,
        "amount": str(order.amount)
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def mark_paid(request):
    order_id = request.data.get('order_id')
    try:
        order = Order.objects.get(order_id=order_id)
        order.status = 'COMPLETED'
        order.save()

        # Send payment success email (async)
        def send_payment_email():
            subject = f"Payment Successful — Order {order.order_id}"
            plain_msg = (
                f"Hello,\n\n"
                f"Thank you for your purchase.\n"
                f"Your payment of ${order.amount} for the report '{order.report.market_name}' "
                f"has been successfully processed.\n\n"
                f"Order ID: {order.order_id}\n"
                f"Report ID: {order.report.report_id}\n"
                f"Estimated Delivery: Within 60 minutes\n\n"
                f"You will receive another email when your analyst-verified report is ready for download.\n\n"
                f"Best,\nForecastly.io Team"
            )

            html_msg = f"""
            <div style="background-color: #F8FAFC; padding: 20px 10px; font-family: 'Inter', system-ui, sans-serif;">
                <div style="max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);">
                    <div style="background: linear-gradient(135deg, #0A3D62 0%, #05283F 100%); padding: 25px 20px; text-align: center;">
                        <div style="font-size: 22px; font-weight: 800; color: #ffffff;">Forecastly.io</div>
                        <div style="font-size: 11px; font-weight: 500; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 1.2px;">Market Intelligence Platform</div>
                    </div>
                    <div style="padding: 30px 25px;">
                        <div style="text-align: center; margin-bottom: 20px;">
                            <div style="width: 56px; height: 56px; border-radius: 50%; background: #D1FAE5; display: inline-flex; align-items: center; justify-content: center; font-size: 1.5rem;">✓</div>
                        </div>
                        <h2 style="font-size: 18px; font-weight: 700; color: #0f172a; text-align: center; margin-bottom: 12px;">Payment Successful</h2>
                        <div style="background: #F8FAFC; border-radius: 12px; padding: 16px; margin: 16px 0; border: 1px solid #E2E8F0;">
                            <table style="width: 100%; font-size: 14px; color: #334155;">
                                <tr><td style="padding: 4px 0; font-weight: 600;">Order ID</td><td style="text-align: right; color: #0A3D62; font-weight: 700;">{order.order_id}</td></tr>
                                <tr><td style="padding: 4px 0; font-weight: 600;">Report</td><td style="text-align: right;">{order.report.market_name}</td></tr>
                                <tr><td style="padding: 4px 0; font-weight: 600;">Amount</td><td style="text-align: right; color: #0A3D62; font-weight: 700;">${order.amount}</td></tr>
                                <tr><td style="padding: 4px 0; font-weight: 600;">Delivery</td><td style="text-align: right;">Within 60 minutes</td></tr>
                            </table>
                        </div>
                        <p style="font-size: 13px; color: #64748B; text-align: center; margin-top: 16px;">
                            Our analysts will review and verify the data before delivering your report via email.
                        </p>
                    </div>
                    <div style="padding: 15px 20px; background: #f8fafc; border-top: 1px solid #f1f5f9; text-align: center;">
                        <p style="font-size: 11px; color: #94a3b8; margin: 0;"><strong>Forecastly.io © 2026</strong> — Analyst-verified datasets.</p>
                    </div>
                </div>
            </div>
            """

            try:
                msg = EmailMultiAlternatives(
                    subject,
                    plain_msg,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@forecastly.io'),
                    [order.user.email]
                )
                msg.attach_alternative(html_msg, "text/html")
                msg.send(fail_silently=True)
            except Exception:
                pass

            # Admin notification
            try:
                admin_email = getattr(settings, 'ADMIN_EMAIL', None)
                if admin_email:
                    send_mail(
                        subject=f"New Order — {order.order_id} — ${order.amount}",
                        message=(
                            f"New order received.\n\n"
                            f"Order ID: {order.order_id}\n"
                            f"Customer: {order.user.email}\n"
                            f"Report: {order.report.market_name} ({order.report.report_id})\n"
                            f"Amount: ${order.amount}\n"
                            f"Payment: {order.payment_method}\n"
                            f"Countries: {order.countries_list}\n"
                            f"Segmentation: {'Yes' if order.has_segmentation else 'No'}\n"
                            f"Global: {'Yes' if order.has_global else 'No'}\n"
                        ),
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@forecastly.io'),
                        recipient_list=[admin_email],
                        fail_silently=True,
                    )
            except Exception:
                pass

        threading.Thread(target=send_payment_email).start()

        return Response({"status": "success"})
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_orders(request):
    email = request.GET.get('email')
    if not email:
        return Response({"error": "Email required"}, status=400)

    try:
        user = User.objects.get(email=email)
        orders = Order.objects.filter(user=user).order_by('-created_at')
        data = []
        for o in orders:
            data.append({
                "id": o.order_id,
                "reportId": o.report.report_id,
                "title": o.report.market_name,
                "total": float(o.amount),
                "status": o.status.lower(),
                "date": o.created_at.strftime('%Y-%m-%d'),
                "has_segmentation": o.has_segmentation,
                "has_global": o.has_global,
                "countries": o.countries_list,
                "payment_method": o.payment_method,
            })
        return Response(data)
    except User.DoesNotExist:
        return Response([])
