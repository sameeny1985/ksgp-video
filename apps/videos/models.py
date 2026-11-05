"""
Video models for KSGP Video Platform
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.users.models import User
from apps.channels.models import Channel
import uuid
import re


class Video(TimeStampedModel, SoftDeleteModel):
    """Video registered on the platform for discovery"""
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PENDING = 'pending', _('Pending Review')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        SUSPENDED = 'suspended', _('Suspended')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='videos')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    youtube_url = models.URLField(help_text='Standard YouTube video URL')
    youtube_video_id = models.CharField(max_length=20, blank=True, db_index=True)
    thumbnail_url = models.URLField(blank=True)
    thumbnail = models.ImageField(upload_to='videos/thumbnails/%Y/%m/', blank=True, null=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey('core.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='videos')
    language = models.CharField(max_length=10, default='en')
    tags = models.ManyToManyField('core.Tag', blank=True, related_name='videos')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    rejection_reason = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_sponsored = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_videos')

    class Meta:
        verbose_name = _('Video')
        verbose_name_plural = _('Videos')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['channel', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured', 'status']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('videos:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if self.youtube_url and not self.youtube_video_id:
            self.youtube_video_id = self.extract_youtube_id(self.youtube_url)
        # Auto title + thumbnail from YouTube when missing
        if self.youtube_url and (not self.title or not self.thumbnail_url or not self.youtube_video_id):
            try:
                from apps.videos.youtube import fetch_youtube_meta
                meta = fetch_youtube_meta(self.youtube_url)
                if meta.get('video_id') and not self.youtube_video_id:
                    self.youtube_video_id = meta['video_id']
                if meta.get('thumbnail_url') and not self.thumbnail_url:
                    self.thumbnail_url = meta['thumbnail_url']
                if meta.get('title') and (not self.title or self.title.startswith('YouTube video')):
                    self.title = meta['title'][:200]
            except Exception:
                pass
        if self.youtube_video_id and not self.thumbnail_url:
            self.thumbnail_url = f'https://img.youtube.com/vi/{self.youtube_video_id}/hqdefault.jpg'
        if not self.title and self.youtube_video_id:
            self.title = f'YouTube video {self.youtube_video_id}'
        super().save(*args, **kwargs)

    @staticmethod
    def extract_youtube_id(url):
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ''

    @property
    def watch_url(self):
        if self.youtube_video_id:
            return f'https://www.youtube.com/watch?v={self.youtube_video_id}'
        return self.youtube_url

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED and self.is_active


class SavedVideo(TimeStampedModel):
    """User saved/favorited videos"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_videos')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='saves')

    class Meta:
        unique_together = ('user', 'video')
        indexes = [models.Index(fields=['user']), models.Index(fields=['video'])]

    def __str__(self):
        return f'{self.user} saved {self.video}'


class VideoView(models.Model):
    """Platform page views of video detail (not YouTube views)"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='platform_views')
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    referrer = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['video', 'created_at']),
        ]
