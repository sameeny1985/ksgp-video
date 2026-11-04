from django.contrib import admin
from .models import ContentReport


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reason', 'status', 'reporter', 'object_type', 'object_id', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('description', 'object_id', 'reporter__email')
