from django.contrib import admin
from .models import Channel, ChannelFollow, ChannelStats


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'category', 'language', 'is_featured', 'is_verified', 'created_at')
    list_filter = ('status', 'is_featured', 'is_verified', 'language', 'category')
    search_fields = ('name', 'youtube_url', 'youtube_channel_id', 'owner__email')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    actions = ['approve_channels', 'reject_channels']

    @admin.action(description='Approve selected channels')
    def approve_channels(self, request, queryset):
        from django.utils import timezone
        queryset.update(status=Channel.Status.APPROVED, approved_at=timezone.now(), approved_by=request.user)

    @admin.action(description='Reject selected channels')
    def reject_channels(self, request, queryset):
        queryset.update(status=Channel.Status.REJECTED)


admin.site.register(ChannelFollow)
admin.site.register(ChannelStats)
