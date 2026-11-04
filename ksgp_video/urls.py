"""
KSGP Video URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from apps.core.sitemaps import StaticViewSitemap, VideoSitemap, ChannelSitemap
from apps.core.views import home, robots_txt, health_check
from apps.core.chain_views import chain_explorer, chain_block_detail

sitemaps = {
    'static': StaticViewSitemap,
    'videos': VideoSitemap,
    'channels': ChannelSitemap,
}

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('rosetta/', include('rosetta.urls')),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('health/', health_check, name='health_check'),
    path('ops/chain/', chain_explorer, name='chain_explorer'),
    path('ops/chain/<int:index>/', chain_block_detail, name='chain_detail'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', home, name='home'),
    path('api/', include('apps.core.api_urls')),
    path('users/', include('apps.users.urls')),
    path('channels/', include('apps.channels.urls')),
    path('videos/', include('apps.videos.urls')),
    path('campaigns/', include('apps.campaigns.urls')),
    path('credits/', include('apps.credits.urls')),
    path('payments/', include('apps.payments.urls')),
    path('ads/', include('apps.ads.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('reports/', include('apps.reports.urls')),
    path('dashboard/', include('apps.core.dashboard_urls')),
    path('about/', TemplateView.as_view(template_name='core/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='core/contact.html'), name='contact'),
    path('terms/', TemplateView.as_view(template_name='core/terms.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='core/privacy.html'), name='privacy'),
    path('cookies/', TemplateView.as_view(template_name='core/cookies.html'), name='cookies'),
    path('advertising-policy/', TemplateView.as_view(template_name='core/advertising_policy.html'), name='advertising_policy'),
    path('creator-guidelines/', TemplateView.as_view(template_name='core/creator_guidelines.html'), name='creator_guidelines'),
    path('faq/', TemplateView.as_view(template_name='core/faq.html'), name='faq'),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin titles
admin.site.site_header = 'KSGP Video Administration'
admin.site.site_title = 'KSGP Video Admin'
admin.site.index_title = 'Platform Management'
