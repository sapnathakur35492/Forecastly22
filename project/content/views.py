from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from .models import SiteSettings, TrustBadge, HowItWorks, Feature, UseCase, FAQ, PricingExample, NavLink, Blog


@api_view(['GET'])
@permission_classes([AllowAny])
def site_config(request):
    """Returns all landing page content in a single JSON response."""
    settings = SiteSettings.load()
    
    return Response({
        'site': {
            'name': settings.site_name,
            'tagline': settings.tagline,
            'footer_text': settings.footer_text,
            'support_email': settings.support_email,
            'support_phone': settings.support_phone,
            'support_chat_hours': settings.support_chat_hours,
        },
        'hero': {
            'badge_text': settings.hero_badge_text,
            'title': settings.hero_title,
            'subtitle': settings.hero_subtitle,
            'search_placeholder': settings.hero_search_placeholder,
            'hint_text': settings.hero_hint_text,
            'excel_preview_title': settings.excel_preview_title,
        },
        'dark_cta': {
            'title': settings.dark_cta_title,
            'text': settings.dark_cta_text,
            'button_text': settings.dark_cta_button_text,
            'note': settings.dark_cta_note,
        },
        'trust_badges': list(TrustBadge.objects.filter(is_active=True).values('icon', 'label', 'sublabel')),
        'how_it_works': list(HowItWorks.objects.filter(is_active=True).values('step_number', 'title', 'description')),
        'features': list(Feature.objects.filter(is_active=True).values('icon', 'title', 'description', 'tags')),
        'use_cases': list(UseCase.objects.filter(is_active=True).values('icon', 'title', 'description')),
        'faqs': list(FAQ.objects.filter(is_active=True).values('question', 'answer')),
        'pricing_examples': list(PricingExample.objects.filter(is_active=True).values('scenario', 'price', 'calculation')),
        'nav_links': list(NavLink.objects.filter(is_active=True).values('label', 'scroll_target', 'url', 'is_cta')),
    })


def blog_list_page(request):
    # Public blog page is always shown in latest-first order.
    blogs = Blog.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'blog_list.html', {'blogs': blogs})


def blog_detail_page(request, slug):
    blog = get_object_or_404(Blog, slug=slug, is_published=True)
    return render(request, 'blog_detail.html', {'blog': blog})
