from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        # Main landing page
        return ['home']

    def location(self, item):
        return '/'

class SectionSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        # These are the logical sections we want indexed
        return ['how-sec', 'price-sec', 'meth-sec', 'faq-sec', 'blog-sec']

    def location(self, item):
        return f'/#{item}'

class BlogSitemap(Sitemap):
    priority = 0.9
    changefreq = 'daily'

    def items(self):
        from content.models import Blog
        return Blog.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return f'/blog/{obj.slug}/'

sitemaps = {
    'static': StaticViewSitemap,
    'sections': SectionSitemap,
    'blog': BlogSitemap,
}
