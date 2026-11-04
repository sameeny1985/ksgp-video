"""
Core views for KSGP Video Platform
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q
from django.utils.translation import gettext as _
from apps.videos.models import Video
from apps.channels.models import Channel
from apps.campaigns.models import Campaign
from apps.core.models import Category, SystemSetting
from apps.ads.services import pick_campaigns_for_page
from django.contrib.auth import get_user_model

User = get_user_model()


def home(request):
    """Homepage - Discover Videos. Connect with Creators. Promote Your Content."""
    featured_videos = Video.objects.filter(
        status=Video.Status.APPROVED,
        is_active=True,
        is_featured=True
    ).select_related('channel', 'category', 'owner')[:12]

    recent_videos = Video.objects.filter(
        status=Video.Status.APPROVED,
        is_active=True
    ).select_related('channel', 'category').order_by('-created_at')[:12]

    featured_channels = Channel.objects.filter(
        status=Channel.Status.APPROVED,
        is_active=True,
        is_featured=True
    ).select_related('category', 'owner')[:8]

    categories = Category.objects.filter(is_featured=True).order_by('order')[:12]

    # Sponsored campaigns via ad engine
    sponsored = pick_campaigns_for_page(request, placement='homepage_grid', limit=6)

    # Platform stats (real counts only)
    stats = {
        'channels': Channel.objects.filter(status=Channel.Status.APPROVED, is_active=True).count(),
        'videos': Video.objects.filter(status=Video.Status.APPROVED, is_active=True).count(),
        'campaigns': Campaign.objects.filter(status=Campaign.Status.ACTIVE).count(),
        'creators': User.objects.filter(role__in=['creator', 'advertiser'], is_active=True).count(),
    }

    context = {
        'featured_videos': featured_videos,
        'recent_videos': recent_videos,
        'featured_channels': featured_channels,
        'categories': categories,
        'sponsored': sponsored,
        'stats': stats,
        'page_title': _('Discover Videos. Connect with Creators. Promote Your Content.'),
    }
    return render(request, 'home/index.html', context)


@require_GET
def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /dashboard/',
        'Disallow: /accounts/',
        'Disallow: /api/',
        f'Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


@require_GET
def health_check(request):
    from apps.core.monitoring import check_system_health
    health = check_system_health()
    status = 200 if health.get('ok') else 503
    return JsonResponse({
        'status': 'ok' if health.get('ok') else 'degraded',
        'service': 'ksgp-video',
        **{k: v for k, v in health.items() if k != 'ok'},
    }, status=status)


