from django.contrib import admin
from .models import Notification, EmailLog

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'email_sent', 'created_at')
    list_filter = ('notification_type', 'is_read', 'email_sent')
    search_fields = ('title', 'user__email')

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('to_email', 'subject', 'status', 'created_at')
    list_filter = ('status',)
    readonly_fields = [f.name for f in EmailLog._meta.fields]
