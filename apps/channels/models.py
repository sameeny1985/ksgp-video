"""
Channel models for KSGP Video Platform
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.users.models import User
import uuid


class Channel(TimeStampedModel, SoftDeleteModel):
    """YouTube Channel registered on platform"""
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending Review')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        SUSPENDED = 'suspended', _('Suspended')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channels')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True)
    youtube_url = models.URLField(help_text='Full YouTube channel URL')
    youtube_channel_id = models.CharField(max_length=50, blank=True, db_index=True)
    avatar = models.ImageField(upload_to='channels/avatars/%Y/%m/', blank=True, null=True)
    banner = models.ImageField(upload_to='channels/banners/%Y/%m/', blank=True, null=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey('core.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='channels')
    language = models.CharField(max_length=10, default='en')
    country = models.CharField(max_length=2, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    rejection_reason = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    subscriber_count_external = models.PositiveIntegerField(default=0, help_text='Optional external data, not for monetization claims')
    view_count_external = models.PositiveBigIntegerField(default=0)
    video_count_external = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField('core.Tag', blank=True, related_name='channels')
    social_links = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_channels')

    class Meta:
        verbose_name = _('Channel')
        verbose_name_plural = _('Channels')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('channels:detail', kwargs={'slug': self.slug})

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED and self.is_active


class ChannelFollow(TimeStampedModel):
    """Users following channels inside the platform"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channel_follows')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='followers')

    class Meta:
        unique_together = ('user', 'channel')
        indexes = [models.Index(fields=['user']), models.Index(fields=['channel'])]

    def __str__(self):
        return f'{self.user} follows {self.channel}'


class ChannelStats(models.Model):
    """Platform-internal stats for channel discovery (not YouTube metrics)"""
    channel = models.OneToOneField(Channel, on_delete=models.CASCADE, related_name='platform_stats')
    profile_views = models.PositiveIntegerField(default=0)
    video_clicks = models.PositiveIntegerField(default=0)
    campaign_impressions = models.PositiveIntegerField(default=0)
    campaign_clicks = models.PositiveIntegerField(default=0)
    followers_count = models.PositiveIntegerField(default=0)
    last_calculated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Stats for {self.channel}'
