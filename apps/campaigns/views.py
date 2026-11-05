from decimal import Decimal

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, TemplateView
)

from .models import Campaign
from apps.credits.models import CreditWallet
from apps.videos.models import Video
from apps.channels.models import Channel


class CampaignCreateForm(forms.ModelForm):

    class Meta:
        model = Campaign
        fields = [
            'name', 'campaign_type', 'pricing_model',
            'ad_title', 'ad_description', 'destination_url',
            'budget', 'daily_budget',
            'start_date', 'end_date',
            'video', 'channel',
        ]

        widgets = {
            'start_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'step': '60',
                    'id': 'id_start_date',
                },
            ),
            'end_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'step': '60',
                    'id': 'id_end_date',
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        date_format = '%Y-%m-%dT%H:%M'

        for field_name in ('start_date', 'end_date'):
            self.fields[field_name].input_formats = [date_format]
            self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        now = timezone.now()

        if start_date and start_date < now:
            self.add_error(
                'start_date',
                _('The campaign start date and time cannot be in the past.')
            )

        if start_date and end_date and end_date <= start_date:
            self.add_error(
                'end_date',
                _('The campaign end date and time must be after the start date and time.')
            )

        return cleaned_data


class CampaignListView(LoginRequiredMixin, ListView):
    model = Campaign
    template_name = 'campaigns/list.html'
    context_object_name = 'campaigns'
    paginate_by = 20

    def get_queryset(self):
        return Campaign.objects.filter(
            owner=self.request.user
        ).order_by('-created_at')


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
    form_class = CampaignCreateForm
    template_name = 'campaigns/form.html'
    success_url = reverse_lazy('dashboard:campaigns')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['video'].queryset = Video.objects.filter(
            owner=self.request.user,
            status=Video.Status.APPROVED
        )

        form.fields['channel'].queryset = Channel.objects.filter(
            owner=self.request.user,
            status=Channel.Status.APPROVED
        )

        form.fields['video'].required = False
        form.fields['channel'].required = False
        form.fields['start_date'].required = False
        form.fields['end_date'].required = False
        form.fields['daily_budget'].required = False

        for field_name in ('start_date', 'end_date'):
            field = form.fields[field_name]

            field.widget = forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'step': '60',
                    'style': 'width:100%; min-height:45px;',
                }
            )

            field.input_formats = ['%Y-%m-%dT%H:%M']

        return form
    def form_valid(self, form):
        user = self.request.user

        campaign = form.save(commit=False)
        campaign.owner = user
        campaign.status = Campaign.Status.DRAFT

        if campaign.pricing_model == Campaign.PricingModel.CPM:
            campaign.cpm_rate = Decimal(
                str(getattr(settings, 'DEFAULT_CPM_RATE', 5.00))
            )

        elif campaign.pricing_model == Campaign.PricingModel.CPC:
            campaign.cpc_rate = Decimal(
                str(getattr(settings, 'DEFAULT_CPC_RATE', 0.25))
            )

        try:
            with transaction.atomic():

                campaign.save()

                wallet = CreditWallet.objects.select_for_update().get(
                    user=user
                )

                if not wallet.can_reserve(campaign.budget):
                    messages.error(
                        self.request,
                        _('Insufficient available credits. Please buy more credits first.')
                    )
                    campaign.delete()
                    return redirect('credits:packages')

                wallet.reserve(
                    campaign.budget,
                    campaign,
                    description=f'Reserve for campaign: {campaign.name}'
                )

                campaign.reserved = campaign.budget
                campaign.status = Campaign.Status.PENDING_REVIEW

                campaign.save(
                    update_fields=['reserved', 'status']
                )

        except Exception as e:
            messages.error(self.request, str(e))
            return redirect('campaigns:create')

        messages.success(
            self.request,
            _('Campaign created and submitted for review. Budget has been reserved.')
        )

        return redirect('dashboard:campaigns')


class CampaignUpdateView(LoginRequiredMixin, UpdateView):
    model = Campaign
    template_name = 'campaigns/form.html'
    fields = [
        'name',
        'ad_title',
        'ad_description',
        'destination_url',
        'end_date'
    ]

    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['end_date'].widget = forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'step': '60',
            }
        )

        form.fields['end_date'].input_formats = [
            '%Y-%m-%dT%H:%M'
        ]

        return form

    def get_queryset(self):
        return Campaign.objects.filter(
            owner=self.request.user
        ).exclude(
            status__in=[
                Campaign.Status.COMPLETED,
                Campaign.Status.CANCELLED
            ]
        )

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Campaign updated.')
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'campaigns:detail',
            kwargs={'uuid': self.object.uuid}
        )


class PricingView(TemplateView):
    template_name = 'campaigns/pricing.html'


def pause_campaign(request, uuid):
    if not request.user.is_authenticated:
        return redirect('account_login')

    campaign = get_object_or_404(
        Campaign,
        uuid=uuid,
        owner=request.user
    )

    if campaign.status == Campaign.Status.ACTIVE:
        campaign.status = Campaign.Status.PAUSED
        campaign.save(update_fields=['status'])

        messages.info(request, _('Campaign paused.'))

    return redirect('dashboard:campaigns')


def resume_campaign(request, uuid):
    if not request.user.is_authenticated:
        return redirect('account_login')

    campaign = get_object_or_404(
        Campaign,
        uuid=uuid,
        owner=request.user
    )

    if (
        campaign.status == Campaign.Status.PAUSED
        and campaign.remaining_budget > 0
    ):
        campaign.status = Campaign.Status.ACTIVE
        campaign.save(update_fields=['status'])

        messages.success(request, _('Campaign resumed.'))

    return redirect('dashboard:campaigns')
