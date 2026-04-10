import random
import logging
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    email = request.data.get('email')
    if not email:
        return Response({"error": "Email is required"}, status=400)

    otp = str(random.randint(100000, 999999))
    
    request.session['otp'] = otp
    request.session['otp_email'] = email
    
    subject = f"{otp} is your Estimately verification code"
    
    # Premium Compact HTML Email Template
    html_message = f"""
    <div style="background-color: #F8FAFC; padding: 20px 10px; font-family: 'Inter', system-ui, -apple-system, sans-serif;">
        <div style="max-width: 460px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);">
            <div style="background-color: #0A3D62; padding: 25px 20px; text-align: center; background: linear-gradient(135deg, #0A3D62 0%, #05283F 100%);">
                <div style="font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; margin-bottom: 2px;">Estimately</div>
                <div style="font-size: 11px; font-weight: 500; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 1.2px;">Market Intelligence Platform</div>
            </div>
            <div style="padding: 30px 25px; text-align: center;">
                <h2 style="font-size: 18px; font-weight: 700; color: #0f172a; margin-top: 0; margin-bottom: 12px;">Access Verification</h2>
                <p style="font-size: 14px; color: #475569; line-height: 1.5; margin: 0;">
                    Enter this code in the builder to unlock your reports.
                </p>
                
                <div style="margin: 25px 0; padding: 20px; background: #FFF7ED; border: 1px solid #FFEDD5; border-radius: 12px;">
                    <span style="font-size: 38px; font-weight: 900; color: #F68B1E; letter-spacing: 6px; font-family: 'Space Grotesk', monospace;">{otp}</span>
                </div>
                
                <p style="font-size: 12px; color: #94a3b8; margin-top: 0;">
                    Valid for 10 minutes.
                </p>
            </div>
            <div style="padding: 15px 20px; background-color: #f8fafc; border-top: 1px solid #f1f5f9; text-align: center;">
                <p style="font-size: 11px; color: #94a3b8; margin: 0; line-height: 1.4;">
                    <strong>Estimately © 2026</strong> — Analyst-verified datasets.
                </p>
            </div>
        </div>
    </div>
    """
    try:
        send_mail(
            subject,
            f"Your verification code is: {otp}",  # Fallback plain text
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
            html_message=html_message
        )
    except Exception as exc:
        import traceback
        error_detail = traceback.format_exc()
        logger.error("OTP email send failed for %s. Error: %s\nDetail: %s", email, str(exc), error_detail)
        return Response({"error": f"OTP email send failed: {str(exc)}"}, status=500)

    return Response({
        "status": "code_sent"
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get('email')
    code = request.data.get('code')
    
    stored_otp = request.session.get('otp')
    stored_email = request.session.get('otp_email')
    
    if code == stored_otp and email == stored_email:
        return Response({"status": "verified"})
    else:
        return Response({"error": "OTP not valid"}, status=400)
