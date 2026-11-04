from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Q
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from apps.channels.models import Channel
from apps.videos.models import Video
from apps.campaigns.models import Campaign
from apps.credits.models import CreditTransaction
from apps.users.models import UserProfile


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        channels = Channel.objects.filter(owner=user, is_active=True)
        videos = Video.objects.filter(owner=user, is_active=True)
        campaigns = Campaign.objects.filter(owner=user)

        ctx['channels_count'] = channels.count()
        ctx['videos_count'] = videos.count()
        ctx['campaigns_active'] = campaigns.filter(status=Campaign.Status.ACTIVE).count()
        ctx['campaigns_total'] = campaigns.count()
        ctx['wallet'] = getattr(user, 'wallet', None)

        # Recent items
        ctx['recent_channels'] = channels.order_by('-created_at')[:5]
        ctx['recent_videos'] = videos.order_by('-created_at')[:5]
        ctx['recent_campaigns'] = campaigns.order_by('-created_at')[:5]

        # Simple stats from campaigns
        active_camps = campaigns.filter(status=Campaign.Status.ACTIVE)
        ctx['total_impressions'] = active_camps.aggregate(total=Sum('impressions'))['total'] or 0
        ctx['total_clicks'] = active_camps.aggregate(total=Sum('clicks'))['total'] or 0

        return ctx


class MyChannelsView(LoginRequiredMixin, ListView):
    model = Channel
    template_name = 'dashboard/channels.html'
    context_object_name = 'channels'
    paginate_by = 12

    def get_queryset(self):
        return Channel.objects.filter(owner=self.request.user).order_by('-created_at')


class MyVideosView(LoginRequiredMixin, ListView):
    model = Video
    template_name = 'dashboard/videos.html'
    context_object_name = 'videos'
    paginate_by = 12

    def get_queryset(self):
        return Video.objects.filter(owner=self.request.user).select_related('channel', 'category').order_by('-created_at')


class MyCampaignsView(LoginRequiredMixin, ListView):
    model = Campaign
    template_name = 'dashboard/campaigns.html'
    context_object_name = 'campaigns'
    paginate_by = 12

    def get_queryset(self):
        return Campaign.objects.filter(owner=self.request.user).order_by('-created_at')


class WalletDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/wallet.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        wallet = getattr(user, 'wallet', None)
        ctx['wallet'] = wallet
        if wallet:
            ctx['transactions'] = CreditTransaction.objects.filter(wallet=wallet).order_by('-created_at')[:30]
        else:
            ctx['transactions'] = []
        return ctx


class SettingsView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    template_name = 'dashboard/settings.html'
    fields = ['display_name', 'bio', 'website', 'location', 'is_public']
    success_url = reverse_lazy('dashboard:settings')

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, _('Profile updated successfully.'))
        return super().form_valid(form)


class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/analytics.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        campaigns = Campaign.objects.filter(owner=user)

        ctx['campaigns'] = campaigns.order_by('-created_at')[:20]
        ctx['total_impressions'] = campaigns.aggregate(t=Sum('impressions'))['t'] or 0
        ctx['total_clicks'] = campaigns.aggregate(t=Sum('clicks'))['t'] or 0
        ctx['total_spent'] = campaigns.aggregate(t=Sum('spent'))['t'] or 0

        # Per campaign summary
        ctx['campaign_stats'] = campaigns.values(
            'name', 'status', 'impressions', 'clicks', 'spent', 'budget'
        ).order_by('-impressions')[:15]

        return ctx
