import os
from django.http import HttpResponse, Http404
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Report, ReportDownloadLog
from .services import generate_excel_report


@api_view(['POST'])
@permission_classes([AllowAny])
def update_report(request, report_id):
    """Update report segments and countries from the builder."""
    try:
        report = Report.objects.get(report_id=report_id)
    except Report.DoesNotExist:
        return Response({"error": "Report not found"}, status=404)

    segments = request.data.get('segments')
    countries = request.data.get('countries')

    if segments is not None:
        # Validate segments structure
        if isinstance(segments, list):
            for seg in segments:
                if not isinstance(seg, dict):
                    return Response({"error": "Invalid segment format"}, status=400)
                subs = seg.get('subsegments', seg.get('items', []))
                if len(subs) > 6:
                    return Response({"error": "Max 6 subsegments per segment"}, status=400)
            if len(segments) > 3:
                return Response({"error": "Max 3 segments allowed"}, status=400)
        report.segments_data['segments'] = segments

    if countries is not None:
        if isinstance(countries, list):
            # Remove duplicates
            countries = list(dict.fromkeys(countries))
        report.countries = countries

    report.save()
    return Response({"status": "success"})


@api_view(['GET'])
@permission_classes([AllowAny])
def download_excel(request, report_id, plan_type):
    """Download Excel report. Supports demo and paid downloads."""
    from orders.models import Order

    # Validate plan_type
    if plan_type not in ('basic', 'professional', 'enterprise'):
        raise Http404("Invalid plan type")

    try:
        report = Report.objects.get(report_id=report_id)
    except Report.DoesNotExist:
        raise Http404("Report not found")

    is_demo = request.GET.get('demo', 'false').lower() == 'true'
    email = request.GET.get('email', '')

    # Defaults
    base_year = request.GET.get('base_year', 2024)
    forecast_year = request.GET.get('forecast_year', 2033)
    metric = request.GET.get('metric', 'Revenue (USD Million)')
    currency = request.GET.get('currency', 'USD')
    countries_to_use = report.countries

    matched_order = None

    # If not demo, verify against completed order
    if not is_demo and email:
        order = Order.objects.filter(
            user__email=email,
            report=report,
            status='COMPLETED'
        ).order_by('-created_at').first()

        if order:
            matched_order = order
            base_year = order.base_year
            forecast_year = order.forecast_year
            metric = order.metric
            currency = order.currency
            # Determine plan from order
            if order.has_segmentation:
                plan_type = 'enterprise'
            else:
                plan_type = 'professional'
            countries_list = [c.strip() for c in order.countries_list.split(',') if c.strip()]
            if order.has_global:
                countries_list = ['Global'] + countries_list
            countries_to_use = countries_list
        else:
            return HttpResponse("No completed order found for this email.", status=403)
    elif is_demo:
        # For demo, use whatever the user has selected
        # Add Global if present in query
        demo_global = request.GET.get('global', 'false').lower() == 'true'
        if demo_global and 'Global' not in countries_to_use:
            countries_to_use = ['Global'] + list(countries_to_use)

    file_rel_path = generate_excel_report(
        report.report_id,
        report.market_name,
        report.segments_data,
        plan_type,
        selected_countries=countries_to_use,
        is_demo=is_demo,
        base_year=base_year,
        forecast_year=forecast_year,
        metric=metric,
        currency=currency
    )
    report.file_path.name = file_rel_path
    report.save()

    full_path = os.path.join(settings.MEDIA_ROOT, report.file_path.name)
    if os.path.exists(full_path):
        with open(full_path, 'rb') as fh:
            forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
            ip = forwarded_for.split(',')[0].strip() if forwarded_for else request.META.get('REMOTE_ADDR', '')
            ReportDownloadLog.objects.create(
                report=report,
                order=matched_order,
                email=email,
                plan_type=plan_type,
                is_demo=is_demo,
                ip_address=ip or '',
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
            )
            response = HttpResponse(
                fh.read(),
                content_type="application/vnd.ms-excel"
            )
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(full_path)}"'
            return response
    raise Http404("File not found")
