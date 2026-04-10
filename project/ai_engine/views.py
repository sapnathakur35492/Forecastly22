from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .services import generate_market_segmentation, parse_segmentation_response, validate_segmentation
from reports.models import Report


@api_view(['POST'])
@permission_classes([AllowAny])
def generate_segmentation(request):
    debug = str(request.query_params.get('debug', '')).strip() in ('1', 'true', 'yes') or bool(request.data.get('debug'))
    market_name = request.data.get('market_name', '').strip()
    if not market_name:
        return Response({"error": "Market name is required"}, status=400)

    from .services import professionalize_market_title, classify_market_domain
    
    # Identify domain first for accurate title professionalization
    domain = classify_market_domain(market_name)
    
    # Case 1 & 2 handling: Generate Professional Title or Fallback
    market_name = professionalize_market_title(market_name, domain)

    raw_text, domain, meta = generate_market_segmentation(market_name)
    parsed_json = parse_segmentation_response(raw_text)

    # Validate: max 3 segments, max 6 subsegments, "Others" always last, domain-aware
    validated_json = validate_segmentation(parsed_json, domain=domain)

    # REGENERATION LAYER: If validation fails or returns an error, force heuristic fallback
    if "error" in validated_json or not validated_json.get("segments"):
        from .services import get_consultant_fallback
        fallback_data = get_consultant_fallback(market_name)
        validated_json = validate_segmentation(fallback_data, domain=domain)

    # Double-check after validation/regeneration
    segs = validated_json.get("segments", [])
    if not segs:
        return Response({"error": "System failure: Unable to generate valid segmentation logic."}, status=500)

    report = Report.objects.create(
        market_name=market_name,
        segments_data=validated_json
    )

    resp = {
        "report_id": report.report_id,
        "market_name": market_name,
        "market_summary": validated_json.get("market_summary", ""),
        "segments": validated_json.get("segments", [])
    }
    if debug:
        resp["debug"] = meta
    return Response(resp)
