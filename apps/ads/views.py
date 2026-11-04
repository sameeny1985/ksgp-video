from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal

from apps.campaigns.models import Campaign, AdImpression, AdClick
from .services import get_eligible_campaigns, pick_ab_variant


@csrf_exempt
@require_POST
def track_impression(request):
    campaign_id = request.POST.get('campaign_id') or request.GET.get('campaign_id')
    placement = request.POST.get('placement', 'discovery_feed')
    if not campaign_id:
        return JsonResponse({'ok': False, 'error': 'missing campaign_id'}, status=400)

    try:
        campaign = Campaign.objects.get(uuid=campaign_id, status=Campaign.Status.ACTIVE)
    except Campaign.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'campaign not found'}, status=404)

    if not campaign.can_serve():
        return JsonResponse({'ok': False, 'error': 'campaign cannot serve'}, status=400)

    session_key = request.session.session_key or ''
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    recent = AdImpression.objects.filter(
        campaign=campaign, session_key=session_key, created_at__gte=today
    ).count()
    if recent >= campaign.frequency_cap_daily:
        return JsonResponse({'ok': False, 'error': 'frequency cap'}, status=429)

    cost = Decimal('0')
    if campaign.pricing_model == Campaign.PricingModel.CPM and campaign.cpm_rate:
        cost = (campaign.cpm_rate / Decimal('1000')).quantize(Decimal('0.000001'))

    imp = AdImpression.objects.create(
        campaign=campaign,
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key,
        placement=placement,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:500],
        cost=cost,
        is_valid=True,
    )

    Campaign.objects.filter(pk=campaign.pk).update(impressions=campaign.impressions + 1)

    if cost > 0 and campaign.reserved >= cost:
        try:
            from apps.credits.models import CreditWallet
            wallet = CreditWallet.objects.get(user=campaign.owner)
            wallet.charge(cost, campaign, description=f'CPM charge impression {imp.id}',
                          idempotency_key=f'imp-{imp.id}')
            campaign.spent += cost
            campaign.reserved = max(Decimal('0'), campaign.reserved - cost)
            campaign.save(update_fields=['spent', 'reserved'])
        except Exception:
            pass

    return JsonResponse({'ok': True, 'impression_id': str(imp.id)})


@require_GET
def track_click(request, campaign_uuid):
    campaign = get_object_or_404(Campaign, uuid=campaign_uuid)
    if campaign.status != Campaign.Status.ACTIVE:
        return HttpResponseRedirect(campaign.destination_url or '/')

    session_key = request.session.session_key or ''
    cost = Decimal('0')
    if campaign.pricing_model == Campaign.PricingModel.CPC and campaign.cpc_rate:
        cost = campaign.cpc_rate

    click = AdClick.objects.create(
        campaign=campaign,
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key,
        placement=request.GET.get('placement', 'unknown'),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:500],
        destination_url=campaign.destination_url,
        cost=cost,
        is_valid=True,
    )

    Campaign.objects.filter(pk=campaign.pk).update(clicks=campaign.clicks + 1)

    if cost > 0 and campaign.reserved >= cost:
        try:
            from apps.credits.models import CreditWallet
            wallet = CreditWallet.objects.get(user=campaign.owner)
            wallet.charge(cost, campaign, description=f'CPC charge click {click.id}',
                          idempotency_key=f'click-{click.id}')
            campaign.spent += cost
            campaign.reserved = max(Decimal('0'), campaign.reserved - cost)
            campaign.save(update_fields=['spent', 'reserved'])
        except Exception:
            pass

    return HttpResponseRedirect(campaign.destination_url or '/')


@require_GET
def get_ads(request):
    """API endpoint to fetch ads for a placement (used by frontend)"""
    placement = request.GET.get('placement', 'discovery_feed')
    limit = min(int(request.GET.get('limit', 3)), 10)
    language = getattr(request, 'LANGUAGE_CODE', 'en')
    session_key = request.session.session_key or ''
    user = request.user if request.user.is_authenticated else None

    campaigns = get_eligible_campaigns(
        placement=placement,
        language=language,
        limit=limit,
        user=user,
        session_key=session_key,
    )

    data = []
    for c in campaigns:
        ab = pick_ab_variant(c, session_key=session_key)
        data.append({
            'id': str(c.uuid),
            'title': ab['title'],
            'description': ab['description'],
            'variant': ab['variant'],
            'destination_url': c.destination_url,
            'click_url': f'/ads/click/{c.uuid}/?placement={placement}',
            'image': c.ad_image.url if c.ad_image else c.ad_image_url,
            'sponsored_label': 'Sponsored',
        })
    return JsonResponse({'ads': data})
