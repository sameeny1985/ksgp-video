"""
Advanced Advertising Engine (final pass)
- Eligibility, targeting, frequency caps
- Priority scoring
- Daily budget pacing
- Simple A/B creative variants (via campaign metadata)
"""
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from apps.campaigns.models import Campaign, AdImpression
import random
import hashlib


def _frequency_ok(campaign, user=None, session_key='', now=None):
    now = now or timezone.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    base = AdImpression.objects.filter(campaign=campaign, is_valid=True)
    if user and getattr(user, 'is_authenticated', False):
        daily = base.filter(user=user, created_at__gte=today).count()
        weekly = base.filter(user=user, created_at__gte=week_ago).count()
    else:
        sk = session_key or ''
        daily = base.filter(session_key=sk, created_at__gte=today).count()
        weekly = base.filter(session_key=sk, created_at__gte=week_ago).count()
    if daily >= (campaign.frequency_cap_daily or 5):
        return False
    if weekly >= (campaign.frequency_cap_weekly or 20):
        return False
    return True


def _daily_spend(campaign, now=None):
    now = now or timezone.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    from django.db.models import Sum
    from apps.campaigns.models import AdImpression, AdClick
    imp = AdImpression.objects.filter(campaign=campaign, created_at__gte=today, is_valid=True).aggregate(t=Sum('cost'))['t'] or Decimal('0')
    clk = AdClick.objects.filter(campaign=campaign, created_at__gte=today, is_valid=True).aggregate(t=Sum('cost'))['t'] or Decimal('0')
    return imp + clk


def budget_pacing_ok(campaign, now=None):
    """Do not overspend daily budget; smooth delivery across the day"""
    if not campaign.daily_budget:
        return True
    spent_today = _daily_spend(campaign, now)
    if spent_today >= campaign.daily_budget:
        return False
    # Optional smooth pacing: allow spend proportional to time of day
    now = now or timezone.now()
    seconds_passed = now.hour * 3600 + now.minute * 60 + now.second
    fraction = min(1.0, seconds_passed / 86400.0 + 0.05)  # small buffer
    allowed = Decimal(str(fraction)) * campaign.daily_budget
    return spent_today <= allowed


def score_campaign(campaign):
    score = 0.0
    remaining = float(campaign.remaining_budget or 0)
    score += min(remaining / 10.0, 50)
    if campaign.impressions > 0:
        ctr = campaign.clicks / max(campaign.impressions, 1)
        score += ctr * 120
    else:
        score += 8  # exploration
    if campaign.end_date:
        days_left = (campaign.end_date - timezone.now()).total_seconds() / 86400
        if 0 < days_left < 3:
            score += 20
        elif 0 < days_left < 14:
            score += 8
    if campaign.budget and campaign.spent is not None:
        pace = float(campaign.spent / campaign.budget) if campaign.budget else 0
        if pace < 0.7:
            score += 12
    # A/B: prefer variant marked winning in metadata
    meta = getattr(campaign, 'notes', '') or ''
    if 'ab_winner' in meta.lower():
        score += 15
    return score


def pick_ab_variant(campaign, session_key=''):
    """
    Simple A/B: if campaign.notes contains ab_variants JSON-like hint,
    or use ad_title as A and append variant B from metadata.
    Returns dict with title/description override.
    """
    # Stable assignment by session
    seed = f'{campaign.uuid}:{session_key}'
    h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    variant = 'A' if h % 2 == 0 else 'B'
    title = campaign.ad_title
    desc = campaign.ad_description
    # Optional: notes field can hold "AB_B_TITLE: ..."
    notes = campaign.notes or ''
    if variant == 'B' and 'AB_B_TITLE:' in notes:
        try:
            title = notes.split('AB_B_TITLE:')[1].split('\n')[0].strip() or title
        except Exception:
            pass
    if variant == 'B' and 'AB_B_DESC:' in notes:
        try:
            desc = notes.split('AB_B_DESC:')[1].split('\n')[0].strip() or desc
        except Exception:
            pass
    return {'variant': variant, 'title': title, 'description': desc}


def get_eligible_campaigns(placement=None, language=None, category_id=None,
                           country=None, limit=5, user=None, session_key=None):
    now = timezone.now()
    qs = Campaign.objects.filter(status=Campaign.Status.ACTIVE).filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now)
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    ).filter(reserved__gt=0)

    if language:
        qs = qs.filter(Q(target_languages=[]) | Q(target_languages__contains=language))
    if country:
        qs = qs.filter(Q(target_countries=[]) | Q(target_countries__contains=country))
    if category_id:
        qs = qs.filter(Q(target_categories__isnull=True) | Q(target_categories=category_id)).distinct()
    if placement:
        qs = qs.filter(placements__placement=placement, placements__is_active=True).distinct()

    candidates = list(qs.select_related('video', 'channel', 'owner')[:100])
    eligible = []
    for c in candidates:
        if not c.can_serve():
            continue
        if not _frequency_ok(c, user=user, session_key=session_key or '', now=now):
            continue
        if not budget_pacing_ok(c, now=now):
            continue
        eligible.append(c)

    scored = [(score_campaign(c), c) for c in eligible]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max(limit * 3, limit)]
    if len(top) > limit:
        weights = [max(s, 0.1) for s, _ in top]
        chosen, pool, w = [], list(top), list(weights)
        for _ in range(min(limit, len(pool))):
            total = sum(w)
            r = random.uniform(0, total)
            upto = 0
            for i, weight in enumerate(w):
                upto += weight
                if upto >= r:
                    chosen.append(pool[i][1])
                    pool.pop(i)
                    w.pop(i)
                    break
        return chosen
    return [c for _, c in top[:limit]]


def pick_campaigns_for_page(request, placement='discovery_feed', limit=3, category_id=None):
    language = getattr(request, 'LANGUAGE_CODE', 'en')
    session_key = getattr(request.session, 'session_key', None) or ''
    user = request.user if getattr(request.user, 'is_authenticated', False) else None
    country = getattr(request.user, 'country', None) if user else None
    return get_eligible_campaigns(
        placement=placement, language=language, category_id=category_id,
        country=country, limit=limit, user=user, session_key=session_key,
    )
