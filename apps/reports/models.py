from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ContentReport(models.Model):
    class Reason(models.TextChoices):
        SPAM = 'spam', _('Spam')
        ILLEGAL = 'illegal', _('Illegal content')
        COPYRIGHT = 'copyright', _('Copyright violation')
        MALICIOUS = 'malicious', _('Malicious link')
        MISLEADING = 'misleading', _('Misleading advertising')
        INAPPROPRIATE = 'inappropriate', _('Inappropriate content')
        IMPERSONATION = 'impersonation', _('Impersonation')
        OTHER = 'other', _('Other')

    class Status(models.TextChoices):
        OPEN = 'open', _('Open')
        REVIEWING = 'reviewing', _('Reviewing')
        RESOLVED = 'resolved', _('Resolved')
        REJECTED = 'rejected', _('Rejected')

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='content_reports'
    )
    reason = models.CharField(max_length=30, choices=Reason.choices)
    description = models.TextField(blank=True)
    object_type = models.CharField(max_length=50, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Report {self.pk} ({self.reason})'
