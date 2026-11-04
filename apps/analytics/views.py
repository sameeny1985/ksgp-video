import csv
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.campaigns.models import Campaign, AdImpression, AdClick


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        days = int(self.request.GET.get('days', 30))
        days = max(1, min(days, 365))
        since = timezone.now() - timedelta(days=days)

        campaigns = Campaign.objects.filter(owner=user)
        ctx['campaigns'] = campaigns.order_by('-created_at')
        ctx['days'] = days

        ctx['total_impressions'] = campaigns.aggregate(t=Sum('impressions'))['t'] or 0
        ctx['total_clicks'] = campaigns.aggregate(t=Sum('clicks'))['t'] or 0
        ctx['total_spent'] = campaigns.aggregate(t=Sum('spent'))['t'] or Decimal('0')
        ctx['total_budget'] = campaigns.aggregate(t=Sum('budget'))['t'] or Decimal('0')

        if ctx['total_impressions']:
            ctx['avg_ctr'] = round((ctx['total_clicks'] / ctx['total_impressions']) * 100, 2)
        else:
            ctx['avg_ctr'] = 0

        impressions_qs = AdImpression.objects.filter(campaign__owner=user, created_at__gte=since, is_valid=True)
        clicks_qs = AdClick.objects.filter(campaign__owner=user, created_at__gte=since, is_valid=True)

        ctx['period_impressions'] = impressions_qs.count()
        ctx['period_clicks'] = clicks_qs.count()
        spend_imp = impressions_qs.aggregate(t=Sum('cost'))['t'] or Decimal('0')
        spend_clk = clicks_qs.aggregate(t=Sum('cost'))['t'] or Decimal('0')
        ctx['period_spend'] = spend_imp + spend_clk

        # Daily series for charts
        labels, imp_data, clk_data = [], [], []
        for i in range(days - 1, -1, -1):
            day = (timezone.now() - timedelta(days=i)).date()
            day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
            day_end = day_start + timedelta(days=1)
            labels.append(day.isoformat())
            imp_data.append(impressions_qs.filter(created_at__gte=day_start, created_at__lt=day_end).count())
            clk_data.append(clicks_qs.filter(created_at__gte=day_start, created_at__lt=day_end).count())

        ctx['chart_labels'] = json.dumps(labels)
        ctx['chart_impressions'] = json.dumps(imp_data)
        ctx['chart_clicks'] = json.dumps(clk_data)

        # By campaign for bar chart
        camp_names, camp_imps, camp_clicks = [], [], []
        ctx['campaign_stats'] = []
        for c in campaigns.order_by('-impressions')[:15]:
            ctr = round((c.clicks / c.impressions) * 100, 2) if c.impressions else 0
            ctx['campaign_stats'].append({
                'name': c.name, 'status': c.get_status_display(),
                'impressions': c.impressions, 'clicks': c.clicks, 'ctr': ctr,
                'spent': c.spent, 'budget': c.budget, 'remaining': c.remaining_budget,
            })
            camp_names.append(c.name[:20])
            camp_imps.append(c.impressions)
            camp_clicks.append(c.clicks)

        ctx['bar_labels'] = json.dumps(camp_names)
        ctx['bar_impressions'] = json.dumps(camp_imps)
        ctx['bar_clicks'] = json.dumps(camp_clicks)

        return ctx


class ChartDataAPI(LoginRequiredMixin, View):
    """JSON API for dynamic charts"""
    def get(self, request):
        user = request.user
        days = int(request.GET.get('days', 30))
        days = max(1, min(days, 365))
        since = timezone.now() - timedelta(days=days)
        impressions_qs = AdImpression.objects.filter(campaign__owner=user, created_at__gte=since, is_valid=True)
        clicks_qs = AdClick.objects.filter(campaign__owner=user, created_at__gte=since, is_valid=True)

        labels, imps, clks = [], [], []
        for i in range(days - 1, -1, -1):
            day = (timezone.now() - timedelta(days=i)).date()
            day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
            day_end = day_start + timedelta(days=1)
            labels.append(day.isoformat())
            imps.append(impressions_qs.filter(created_at__gte=day_start, created_at__lt=day_end).count())
            clks.append(clicks_qs.filter(created_at__gte=day_start, created_at__lt=day_end).count())

        return JsonResponse({'labels': labels, 'impressions': imps, 'clicks': clks})


class ExportCSVView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        campaigns = Campaign.objects.filter(owner=user).order_by('-created_at')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ksgp_campaign_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Campaign', 'Type', 'Status', 'Budget EUR', 'Spent EUR', 'Impressions', 'Clicks', 'CTR %', 'Created'])
        for c in campaigns:
            ctr = round((c.clicks / c.impressions) * 100, 2) if c.impressions else 0
            writer.writerow([c.name, c.get_campaign_type_display(), c.get_status_display(),
                             c.budget, c.spent, c.impressions, c.clicks, ctr,
                             c.created_at.strftime('%Y-%m-%d %H:%M')])
        return response
