from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from decimal import Decimal

from .models import Campaign
from apps.credits.models import CreditWallet
from apps.videos.models import Video
from apps.channels.models import Channel


class CampaignListView(LoginRequiredMixin, ListView):
    model = Campaign
    template_name = 'campaigns/list.html'
    context_object_name = 'campaigns'
    paginate_by = 20

    def get_queryset(self):
        return Campaign.objects.filter(owner=self.request.user).order_by('-created_at')


class CampaignDetailView(LoginRequiredMixin, DetailView):
    model = Campaign
    template_name = 'campaigns/detail.html'
    context_object_name = 'campaign'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_queryset(self):
        return Campaign.objects.filter(owner=self.request.user)


class CampaignCreateView(LoginRequiredMixin, CreateView):
    model = Campaign
    template_name = 'campaigns/form.html'
    fields = [
        'name', 'campaign_type', 'pricing_model',
        'ad_title', 'ad_description', 'destination_url',
        'budget', 'daily_budget',
        'start_date', 'end_date',
        'video', 'channel',
    ]
    success_url = reverse_lazy('dashboard:campaigns')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['video'].queryset = Video.objects.filter(owner=self.request.user, status=Video.Status.APPROVED)
        form.fields['channel'].queryset = Channel.objects.filter(owner=self.request.user, status=Channel.Status.APPROVED)
        form.fields['video'].required = False
        form.fields['channel'].required = False
        form.fields['start_date'].required = False
        form.fields['end_date'].required = False
        form.fields['daily_budget'].required = False
        return form

    def form_valid(self, form):
        user = self.request.user
        campaign = form.save(commit=False)
        campaign.owner = user
        campaign.status = Campaign.Status.DRAFT

        from django.conf import settings
        if campaign.pricing_model == Campaign.PricingModel.CPM:
            campaign.cpm_rate = Decimal(str(getattr(settings, 'DEFAULT_CPM_RATE', 5.00)))
        elif campaign.pricing_model == Campaign.PricingModel.CPC:
            campaign.cpc_rate = Decimal(str(getattr(settings, 'DEFAULT_CPC_RATE', 0.25)))

        try:
            with transaction.atomic():
                campaign.save()
                wallet = CreditWallet.objects.select_for_update().get(user=user)
                if not wallet.can_reserve(campaign.budget):
                    messages.error(self.request, _('Insufficient available credits. Please buy more credits first.'))
                    campaign.delete()
                    return redirect('credits:packages')
                wallet.reserve(campaign.budget, campaign, description=f'Reserve for campaign: {campaign.name}')
                campaign.reserved = campaign.budget
                campaign.status = Campaign.Status.PENDING_REVIEW
                campaign.save(update_fields=['reserved', 'status'])
        except Exception as e:
            messages.error(self.request, str(e))
            return redirect('campaigns:create')

        messages.success(self.request, _('Campaign created and submitted for review. Budget has been reserved.'))
        return redirect('dashboard:campaigns')


class CampaignUpdateView(LoginRequiredMixin, UpdateView):
    model = Campaign
    template_name = 'campaigns/form.html'
    fields = ['name', 'ad_title', 'ad_description', 'destination_url', 'end_date']
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_queryset(self):
        return Campaign.objects.filter(owner=self.request.user).exclude(
            status__in=[Campaign.Status.COMPLETED, Campaign.Status.CANCELLED]
        )

    def form_valid(self, form):
        messages.success(self.request, _('Campaign updated.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('campaigns:detail', kwargs={'uuid': self.object.uuid})


class PricingView(TemplateView):
    template_name = 'campaigns/pricing.html'


def pause_campaign(request, uuid):
    if not request.user.is_authenticated:
        return redirect('account_login')
    campaign = get_object_or_404(Campaign, uuid=uuid, owner=request.user)
    if campaign.status == Campaign.Status.ACTIVE:
        campaign.status = Campaign.Status.PAUSED
        campaign.save(update_fields=['status'])
        messages.info(request, _('Campaign paused.'))
    return redirect('dashboard:campaigns')


def resume_campaign(request, uuid):
    if not request.user.is_authenticated:
        return redirect('account_login')
    campaign = get_object_or_404(Campaign, uuid=uuid, owner=request.user)
    if campaign.status == Campaign.Status.PAUSED and campaign.remaining_budget > 0:
        campaign.status = Campaign.Status.ACTIVE
        campaign.save(update_fields=['status'])
        messages.success(request, _('Campaign resumed.'))
    return redirect('dashboard:campaigns')
