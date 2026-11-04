from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.videos.models import Video
from apps.channels.models import Channel

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    def items(self):
        return ['home', 'about', 'contact', 'faq', 'terms', 'privacy']
    def location(self, item):
        return reverse(item)

class VideoSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.7
    def items(self):
        return Video.objects.filter(status='approved', is_active=True)[:1000]
    def lastmod(self, obj):
        return obj.updated_at

class ChannelSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6
    def items(self):
        return Channel.objects.filter(status='approved', is_active=True)[:500]
