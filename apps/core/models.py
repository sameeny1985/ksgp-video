"""
Core models for KSGP Video Platform
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
import uuid


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Abstract model supporting soft delete"""
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    """Content categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='Font Awesome or Bootstrap icon class')
    color = models.CharField(max_length=7, default='#6366f1')
    order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('videos:category', kwargs={'slug': self.slug})


class Tag(TimeStampedModel):
    """Tags for videos and channels"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    usage_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-usage_count', 'name']

    def __str__(self):
        return self.name


class SystemSetting(models.Model):
    """Key-value system settings managed by admin"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    value_type = models.CharField(max_length=20, choices=[
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ], default='string')
    description = models.CharField(max_length=255, blank=True)
    is_public = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('System Setting')
        verbose_name_plural = _('System Settings')

    def __str__(self):
        return self.key

    @classmethod
    def get(cls, key, default=None):
        cache_key = f'system_setting_{key}'
        value = cache.get(cache_key)
        if value is None:
            try:
                setting = cls.objects.get(key=key)
                value = setting.value
                if setting.value_type == 'integer':
                    value = int(value)
                elif setting.value_type == 'float':
                    value = float(value)
                elif setting.value_type == 'boolean':
                    value = value.lower() in ('true', '1', 'yes')
                elif setting.value_type == 'json':
                    import json
                    value = json.loads(value)
                cache.set(cache_key, value, 300)
            except cls.DoesNotExist:
                value = default
        return value

    @classmethod
    def set(cls, key, value, value_type='string', description=''):
        obj, _ = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': str(value),
                'value_type': value_type,
                'description': description,
            }
        )
        cache.delete(f'system_setting_{key}')
        return obj


class Language(models.Model):
    """Supported languages"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    native_name = models.CharField(max_length=50)
    is_rtl = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f'{self.name} ({self.code})'


class PageContent(TimeStampedModel):
    """CMS-like static page content"""
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Page Content')
        verbose_name_plural = _('Page Contents')

    def __str__(self):
        return self.title


class AuditLog(models.Model):
    """Immutable audit log for sensitive operations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100, db_index=True)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f'{self.action} at {self.created_at}'


class ChainBlock(models.Model):
    """Append-only hash-linked audit block (admin integrity chain, not crypto currency)."""
    index = models.PositiveBigIntegerField(unique=True, db_index=True)
    prev_hash = models.CharField(max_length=64)
    block_hash = models.CharField(max_length=64, unique=True, db_index=True)
    event_type = models.CharField(max_length=64, db_index=True)
    actor = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='chain_events')
    actor_email = models.EmailField(blank=True)
    object_type = models.CharField(max_length=64, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ['-index']
        verbose_name = 'Audit Chain Block'
        verbose_name_plural = 'Audit Chain Blocks'

    def __str__(self):
        return f'#{self.index} {self.event_type} {self.block_hash[:12]}'

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError('Chain blocks are immutable')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('Chain blocks cannot be deleted')
