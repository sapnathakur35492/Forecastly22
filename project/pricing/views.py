from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import PricingSettings, Region


@api_view(['GET'])
@permission_classes([AllowAny])
def pricing_config(request):
    """Returns all pricing parameters for the frontend calculator."""
    p = PricingSettings.load()
    return Response({
        'per_country_price': p.per_country_price,
        'global_price': p.global_price,
        'segmentation_price': p.segmentation_price,
        'pro_cap': p.pro_cap,
        'pro_cap_threshold': p.pro_cap_threshold,
        'enterprise_cap': p.enterprise_cap,
        'extra_country_price': p.extra_country_price,
        'both_metric_multiplier': float(p.both_metric_multiplier),
        'min_order': p.min_order,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def regions_list(request):
    """Returns all active regions with their countries for the builder."""
    regions = Region.objects.filter(is_active=True).prefetch_related('countries')
    data = []
    for region in regions:
        countries = region.countries.filter(is_active=True).order_by('display_order')
        data.append({
            'name': region.name,
            'slug': region.slug,
            'countries': [
                {
                    'name': c.name,
                    'is_default': c.is_default,
                    'is_rest_of': c.is_rest_of,
                }
                for c in countries
            ]
        })
    return Response(data)
