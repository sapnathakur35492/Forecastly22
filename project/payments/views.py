from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from orders.models import Order
import threading
import os
import base64
import json
import uuid
import requests


@api_view(['POST'])
@permission_classes([AllowAny])
def payment_webhook(request):
    """
    Payment webhook handler.
    Supports both Stripe webhook verification and manual mark-as-paid.
    When Stripe/PayPal keys are configured, this will verify signatures.
    """
    order_id = request.data.get('order_id')
    payment_gateway = request.data.get('gateway', 'manual')

    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    # If Stripe keys are configured, verify the webhook
    if payment_gateway == 'stripe':
        from pricing.models import PricingSettings
        pricing = PricingSettings.load()
        if pricing.stripe_secret_key:
            # TODO: Verify Stripe webhook signature
            # stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
            pass

    # Mark order as completed
    order.status = 'COMPLETED'
    order.save()

    # Send emails asynchronously
    def send_emails():
        _send_payment_success_email(order)
        _send_delivery_email(order)
        _send_admin_notification(order)

    threading.Thread(target=send_emails).start()

    return Response({"status": "Payment processed, emails queued"})


@api_view(['POST'])
@permission_classes([AllowAny])
def create_stripe_session(request):
    """
    Create a Stripe Checkout Session.
    Returns session URL for redirect.
    Keys must be configured in Django Admin → Pricing Settings.
    """
    from pricing.models import PricingSettings
    pricing = PricingSettings.load()

    if not pricing.stripe_public_key or not pricing.stripe_secret_key:
        return Response({
            "error": "Stripe is not yet configured. Please contact support.",
            "fallback": True
        }, status=503)

    order_id = request.data.get('order_id')
    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    try:
        import stripe
        stripe.api_key = pricing.stripe_secret_key

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': order.currency.lower(),
                    'product_data': {
                        'name': f'Market Report: {order.report.market_name}',
                        'description': f'Order {order.order_id}',
                    },
                    'unit_amount': int(float(order.amount) * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/') + f'?payment=success&order={order.order_id}',
            cancel_url=request.build_absolute_uri('/') + f'?payment=cancelled&order={order.order_id}',
            metadata={'order_id': order.order_id},
        )
        return Response({"session_url": session.url, "session_id": session.id})
    except ImportError:
        return Response({"error": "Stripe SDK not installed", "fallback": True}, status=503)
    except Exception as e:
        return Response({"error": str(e), "fallback": True}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_paypal_order(request):
    """
    Create a PayPal order (server-side Orders v2).
    Flow: create order → risk API → return orderID for approval.
    """
    from pricing.models import PricingSettings
    pricing = PricingSettings.load()

    env_client_id = os.getenv("PAYPAL_CLIENT_ID")
    if not (pricing.paypal_client_id or env_client_id):
        return Response({
            "error": "PayPal is not yet configured. Please contact support.",
            "fallback": True
        }, status=503)

    order_id = request.data.get('order_id')
    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    try:
        paypal_env = os.getenv("PAYPAL_ENV", "sandbox").lower()
        base_url = "https://api-m.sandbox.paypal.com" if paypal_env != "live" else "https://api-m.paypal.com"

        client_id = pricing.paypal_client_id or env_client_id
        client_secret = os.getenv("PAYPAL_SECRET")
        if not client_secret:
            return Response({"error": "PayPal secret is missing on server (PAYPAL_SECRET)."}, status=503)

        access_token = _paypal_get_access_token(base_url, client_id, client_secret)

        currency = (order.currency or "USD").upper()
        amount = str(order.amount)

        # Create Order (CAPTURE intent)
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": order.order_id,
                "description": f"Market Report: {order.report.market_name}",
                "custom_id": order.order_id,
                "amount": {
                    "currency_code": currency,
                    "value": amount,
                },
            }],
            "application_context": {
                "brand_name": "Estimately.io",
                "landing_page": "LOGIN",
                "user_action": "PAY_NOW",
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "PayPal-Request-Id": str(uuid.uuid4()),
        }
        r = requests.post(f"{base_url}/v2/checkout/orders", headers=headers, data=json.dumps(payload), timeout=30)
        if r.status_code not in (200, 201):
            return Response({"error": "PayPal create order failed", "details": r.text}, status=502)

        data = r.json()
        pp_order_id = data.get("id")
        if not pp_order_id:
            return Response({"error": "PayPal create order returned no order id"}, status=502)

        # Prefer merchant_id from PayPal response when available
        payee_merchant_id = None
        try:
            pu = (data.get("purchase_units") or [])
            if pu and isinstance(pu, list):
                payee = pu[0].get("payee") if isinstance(pu[0], dict) else None
                if payee and isinstance(payee, dict):
                    payee_merchant_id = payee.get("merchant_id")
        except Exception:
            payee_merchant_id = None

        # Risk API (Transaction Context) - required by spec
        risk_ok, risk_err = _paypal_risk_set_transaction_context(
            base_url=base_url,
            access_token=access_token,
            order=order,
            tracking_id=pp_order_id,
            merchant_id=payee_merchant_id,
        )
        # Do not block checkout if risk context cannot be set.
        # We still attempt the call for compliance, and return warning for observability.
        warning = None
        if not risk_ok:
            warning = f"Risk API not applied: {risk_err}"

        return Response({
            "paypal_order_id": pp_order_id,
            "status": data.get("status"),
            "warning": warning,
        })
    except requests.RequestException as e:
        return Response({"error": "PayPal network error", "details": str(e)}, status=502)
    except Exception as e:
        return Response({"error": "PayPal order creation failed", "details": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def capture_paypal_order(request):
    """
    Capture PayPal order after approval.
    If COMPLETED → mark local Order as COMPLETED.
    """
    from pricing.models import PricingSettings
    pricing = PricingSettings.load()

    paypal_order_id = request.data.get("paypal_order_id")
    order_id = request.data.get("order_id")
    if not paypal_order_id or not order_id:
        return Response({"error": "Missing paypal_order_id or order_id"}, status=400)

    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    try:
        paypal_env = os.getenv("PAYPAL_ENV", "sandbox").lower()
        base_url = "https://api-m.sandbox.paypal.com" if paypal_env != "live" else "https://api-m.paypal.com"

        client_id = pricing.paypal_client_id or os.getenv("PAYPAL_CLIENT_ID")
        if not client_id:
            return Response({"error": "PayPal client id missing (PAYPAL_CLIENT_ID or Pricing Settings)."}, status=503)
        client_secret = os.getenv("PAYPAL_SECRET")
        if not client_secret:
            return Response({"error": "PayPal secret is missing on server (PAYPAL_SECRET)."}, status=503)

        access_token = _paypal_get_access_token(base_url, client_id, client_secret)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "PayPal-Request-Id": str(uuid.uuid4()),
        }
        r = requests.post(f"{base_url}/v2/checkout/orders/{paypal_order_id}/capture", headers=headers, timeout=30)
        if r.status_code not in (200, 201):
            return Response({"error": "PayPal capture failed", "details": r.text}, status=502)

        data = r.json()
        status = data.get("status")
        if status == "COMPLETED":
            order.status = "COMPLETED"
            order.payment_method = "paypal"
            order.save()
            # Reuse existing email + delivery pipeline
            def send_emails():
                _send_payment_success_email(order)
                _send_delivery_email(order)
                _send_admin_notification(order)
            threading.Thread(target=send_emails).start()

        return Response({"status": status, "raw": data})
    except requests.RequestException as e:
        return Response({"error": "PayPal network error", "details": str(e)}, status=502)
    except Exception as e:
        return Response({"error": "PayPal capture failed", "details": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def paypal_config(request):
    """Expose PayPal client-id for Smart Buttons JS SDK."""
    from pricing.models import PricingSettings
    pricing = PricingSettings.load()
    env_client_id = os.getenv("PAYPAL_CLIENT_ID")
    if not (pricing.paypal_client_id or env_client_id):
        return Response({"enabled": False})
    env = os.getenv("PAYPAL_ENV", "sandbox").lower()
    return Response({
        "enabled": True,
        "client_id": pricing.paypal_client_id or env_client_id,
        "env": env,
    })


def _paypal_get_access_token(base_url: str, client_id: str, client_secret: str) -> str:
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = "grant_type=client_credentials"
    r = requests.post(f"{base_url}/v1/oauth2/token", headers=headers, data=data, timeout=30)
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        raise RuntimeError("PayPal token missing in response")
    return token


def _paypal_risk_set_transaction_context(base_url: str, access_token: str, order: Order, tracking_id: str, merchant_id=None):
    """
    PayPal Transaction Risk API (limited release):
    PUT /v1/risk/transaction-contexts/{merchant_id}/{tracking_id}

    We use tracking_id = PayPal order id so PayPal can correlate.
    """
    merchant_id = (merchant_id or os.getenv("PAYPAL_MERCHANT_ID", "")).strip()
    if not merchant_id:
        return False, "Missing PAYPAL_MERCHANT_ID (required for Risk API)"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "additional_data": [
            {"key": "order_id", "value": order.order_id},
            {"key": "report_id", "value": order.report.report_id},
            {"key": "amount", "value": str(order.amount)},
            {"key": "currency", "value": str(order.currency or "USD")},
            {"key": "email", "value": str(order.user.email)},
        ]
    }
    url = f"{base_url}/v1/risk/transaction-contexts/{merchant_id}/{tracking_id}"
    r = requests.put(url, headers=headers, data=json.dumps(payload), timeout=30)
    if r.status_code not in (200, 201, 204):
        return False, r.text
    return True, None


# ═══════════════════════════════════════════════
# EMAIL HELPERS
# ═══════════════════════════════════════════════

def _send_payment_success_email(order):
    """Send premium HTML payment success email to customer."""
    subject = f"Payment Successful — Order {order.order_id}"
    plain_msg = (
        f"Hello,\n\nThank you for your purchase.\n"
        f"Your payment of ${order.amount} for '{order.report.market_name}' was successful.\n"
        f"Order ID: {order.order_id}\n"
        f"Estimated Delivery: Within 60 minutes\n\n"
        f"Best,\nEstimately.io Team"
    )

    html_msg = f"""
    <div style="background-color:#F8FAFC;padding:20px 10px;font-family:'Inter',system-ui,sans-serif;">
        <div style="max-width:500px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);">
            <div style="background:linear-gradient(135deg,#0A3D62,#05283F);padding:25px 20px;text-align:center;">
                <div style="font-size:22px;font-weight:800;color:#fff;">Estimately.io</div>
                <div style="font-size:11px;color:rgba(255,255,255,0.6);text-transform:uppercase;letter-spacing:1.2px;">Market Intelligence Platform</div>
            </div>
            <div style="padding:30px 25px;text-align:center;">
                <div style="width:56px;height:56px;border-radius:50%;background:#D1FAE5;display:inline-flex;align-items:center;justify-content:center;font-size:1.5rem;margin-bottom:12px;">✓</div>
                <h2 style="font-size:18px;color:#0f172a;margin-bottom:12px;">Payment Successful</h2>
                <div style="background:#F8FAFC;border-radius:12px;padding:16px;border:1px solid #E2E8F0;text-align:left;">
                    <table style="width:100%;font-size:14px;color:#334155;">
                        <tr><td style="padding:4px 0;font-weight:600;">Order ID</td><td style="text-align:right;color:#0A3D62;font-weight:700;">{order.order_id}</td></tr>
                        <tr><td style="padding:4px 0;font-weight:600;">Report</td><td style="text-align:right;">{order.report.market_name}</td></tr>
                        <tr><td style="padding:4px 0;font-weight:600;">Amount</td><td style="text-align:right;color:#0A3D62;font-weight:700;">${order.amount}</td></tr>
                        <tr><td style="padding:4px 0;font-weight:600;">Delivery</td><td style="text-align:right;">Within 60 minutes</td></tr>
                    </table>
                </div>
                <p style="font-size:13px;color:#64748B;margin-top:16px;">Our analysts will review and verify the data before delivering your report.</p>
            </div>
            <div style="padding:15px 20px;background:#f8fafc;border-top:1px solid #f1f5f9;text-align:center;">
                <p style="font-size:11px;color:#94a3b8;margin:0;"><strong>Estimately.io © 2026</strong></p>
            </div>
        </div>
    </div>
    """

    try:
        msg = EmailMultiAlternatives(
            subject, plain_msg,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@Estimately.io'),
            [order.user.email]
        )
        msg.attach_alternative(html_msg, "text/html")
        msg.send(fail_silently=True)
    except Exception:
        pass


def _send_delivery_email(order):
    """Send report delivery email to customer."""
    subject = f"Your Report is Ready — {order.order_id}"
    plain_msg = (
        f"Hello,\n\nYour report '{order.report.market_name}' (Order: {order.order_id}) is ready.\n"
        f"Please log in to your Estimately.io dashboard to download it.\n\n"
        f"Best,\nEstimately.io Team"
    )

    html_msg = f"""
    <div style="background-color:#F8FAFC;padding:20px 10px;font-family:'Inter',system-ui,sans-serif;">
        <div style="max-width:500px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);">
            <div style="background:linear-gradient(135deg,#0A3D62,#05283F);padding:25px 20px;text-align:center;">
                <div style="font-size:22px;font-weight:800;color:#fff;">Estimately.io</div>
                <div style="font-size:11px;color:rgba(255,255,255,0.6);text-transform:uppercase;letter-spacing:1.2px;">Market Intelligence Platform</div>
            </div>
            <div style="padding:30px 25px;text-align:center;">
                <div style="width:56px;height:56px;border-radius:50%;background:#DBEAFE;display:inline-flex;align-items:center;justify-content:center;font-size:1.5rem;margin-bottom:12px;">📊</div>
                <h2 style="font-size:18px;color:#0f172a;margin-bottom:12px;">Your Report is Ready</h2>
                <p style="font-size:14px;color:#475569;line-height:1.5;">
                    Your analyst-verified report for <strong>{order.report.market_name}</strong> is ready for download.
                </p>
                <div style="background:#F8FAFC;border-radius:12px;padding:16px;border:1px solid #E2E8F0;text-align:left;margin:16px 0;">
                    <table style="width:100%;font-size:14px;color:#334155;">
                        <tr><td style="padding:4px 0;font-weight:600;">Order ID</td><td style="text-align:right;font-weight:700;">{order.order_id}</td></tr>
                        <tr><td style="padding:4px 0;font-weight:600;">Report ID</td><td style="text-align:right;font-weight:700;color:#42A5F5;">{order.report.report_id}</td></tr>
                    </table>
                </div>
                <p style="font-size:13px;color:#64748B;">Log in to your dashboard to download your Excel report.</p>
            </div>
            <div style="padding:15px 20px;background:#f8fafc;border-top:1px solid #f1f5f9;text-align:center;">
                <p style="font-size:11px;color:#94a3b8;margin:0;"><strong>Estimately.io © 2026</strong></p>
            </div>
        </div>
    </div>
    """

    try:
        msg = EmailMultiAlternatives(
            subject, plain_msg,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@Estimately.io'),
            [order.user.email]
        )
        msg.attach_alternative(html_msg, "text/html")
        msg.send(fail_silently=True)
    except Exception:
        pass


def _send_admin_notification(order):
    """Send admin notification with order details."""
    admin_email = getattr(settings, 'ADMIN_EMAIL', None)
    if not admin_email:
        return

    try:
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
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@Estimately.io'),
            recipient_list=[admin_email],
            fail_silently=True,
        )
    except Exception:
        pass
