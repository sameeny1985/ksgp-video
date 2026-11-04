"""
Campaign & Advertising models for KSGP Video Platform
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.core.models import TimeStampedModel
from apps.users.models import User
from apps.channels.models import Channel
from apps.videos.models import Video
import uuid


class Campaign(TimeStampedModel):
    """Advertising Campaign"""
    class Type(models.TextChoices):
        VIDEO_PROMOTION = 'video_promotion', _('Video Promotion')
        CHANNEL_PROMOTION = 'channel_promotion', _('Channel Promotion')
        HOMEPAGE_FEATURED = 'homepage_featured', _('Homepage Featured')
        CATEGORY_FEATURED = 'category_featured', _('Category Featured')
        SEARCH_SPONSORED = 'search_sponsored', _('Search Sponsored')
        CREATOR_SPOTLIGHT = 'creator_spotlight', _('Creator Spotlight')
        BRAND_CAMPAIGN = 'brand_campaign', _('Brand Campaign')

    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PENDING_REVIEW = 'pending_review', _('Pending Review')
        APPROVED = 'approved', _('Approved')
        SCHEDULED = 'scheduled', _('Scheduled')
        ACTIVE = 'active', _('Active')
        PAUSED = 'paused', _('Paused')
        COMPLETED = 'completed', _('Completed')
        REJECTED = 'rejected', _('Rejected')
        CANCELLED = 'cancelled', _('Cancelled')

    class PricingModel(models.TextChoices):
        CPM = 'cpm', _('CPM - Cost Per Mille')
        CPC = 'cpc', _('CPC - Cost Per Click')
        FIXED = 'fixed', _('Fixed Placement')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField(max_length=150)
    campaign_type = models.CharField(max_length=30, choices=Type.choices, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    pricing_model = models.CharField(max_length=10, choices=PricingModel.choices, default=PricingModel.CPM)
    
    # Target content
    video = models.ForeignKey(Video, null=True, blank=True, on_delete=models.SET_NULL, related_name='campaigns')
    channel = models.ForeignKey(Channel, null=True, blank=True, on_delete=models.SET_NULL, related_name='campaigns')
    
    # Creative
    ad_title = models.CharField(max_length=100)
    ad_description = models.TextField(max_length=300)
    ad_image = models.ImageField(upload_to='campaigns/ads/%Y/%m/', blank=True, null=True)
    ad_image_url = models.URLField(blank=True)
    destination_url = models.URLField(help_text='Usually YouTube link')
    
    # Budget & Schedule
    budget = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('1.00'))])
    spent = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    reserved = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    daily_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cpm_rate = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    cpc_rate = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    fixed_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Targeting
    target_languages = models.JSONField(default=list, blank=True)
    target_countries = models.JSONField(default=list, blank=True)
    target_categories = models.ManyToManyField('core.Category', blank=True, related_name='targeted_campaigns')
    
    # Limits
    max_impressions = models.PositiveIntegerField(null=True, blank=True)
    max_clicks = models.PositiveIntegerField(null=True, blank=True)
    frequency_cap_daily = models.PositiveIntegerField(default=5)
    frequency_cap_weekly = models.PositiveIntegerField(default=20)
    
    # Moderation
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_campaigns')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Stats (denormalized for performance)
    impressions = models.PositiveIntegerField(default=0)
    unique_impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    unique_clicks = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('Campaign')
        verbose_name_plural = _('Campaigns')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'campaign_type']),
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'

    @property
    def remaining_budget(self):
        return self.budget - self.spent - self.reserved

    @property
    def ctr(self):
        if self.impressions == 0:
            return Decimal('0.00')
        return (Decimal(self.clicks) / Decimal(self.impressions) * 100).quantize(Decimal('0.01'))

    @property
    def is_active_now(self):
        now = timezone.now()
        if self.status != self.Status.ACTIVE:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        if self.remaining_budget <= 0:
            return False
        return True

    def can_serve(self):
        return self.is_active_now and self.remaining_budget > 0


class CampaignPlacement(TimeStampedModel):
    """Where the ad can appear"""
    class Placement(models.TextChoices):
        HOMEPAGE_HERO = 'homepage_hero', _('Homepage Hero')
        HOMEPAGE_SIDEBAR = 'homepage_sidebar', _('Homepage Sidebar')
        HOMEPAGE_GRID = 'homepage_grid', _('Homepage Grid')
        CATEGORY_TOP = 'category_top', _('Category Top')
        SEARCH_RESULTS = 'search_results', _('Search Results')
        VIDEO_DETAIL = 'video_detail', _('Video Detail Sidebar')
        CHANNEL_DETAIL = 'channel_detail', _('Channel Detail')
        DISCOVERY_FEED = 'discovery_feed', _('Discovery Feed')

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='placements')
    placement = models.CharField(max_length=30, choices=Placement.choices)
    priority = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('campaign', 'placement')

    def __str__(self):
        return f'{self.campaign.name} - {self.get_placement_display()}'


class AdImpression(models.Model):
    """Record of ad impression (valid view)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='impression_logs')
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    placement = models.CharField(max_length=30)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    country = models.CharField(max_length=2, blank=True)
    language = models.CharField(max_length=10, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.000000'))
    is_valid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['campaign', 'created_at']),
            models.Index(fields=['session_key', 'campaign', 'created_at']),
            models.Index(fields=['user', 'campaign', 'created_at']),
        ]


class AdClick(models.Model):
    """Record of valid ad click"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='click_logs')
    impression = models.ForeignKey(AdImpression, null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    placement = models.CharField(max_length=30)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    destination_url = models.URLField()
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.000000'))
    is_valid = models.BooleanField(default=True)
    is_unique = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['campaign', 'created_at']),
            models.Index(fields=['session_key', 'campaign']),
        ]
