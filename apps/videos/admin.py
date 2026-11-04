from django.contrib import admin
from .models import Video, SavedVideo, VideoView


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'channel', 'owner', 'status', 'category', 'language', 'is_featured', 'is_sponsored', 'created_at')
    list_filter = ('status', 'is_featured', 'is_sponsored', 'language', 'category')
    search_fields = ('title', 'youtube_url', 'youtube_video_id', 'owner__email', 'channel__name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('uuid', 'youtube_video_id', 'created_at', 'updated_at')
    actions = ['approve_videos', 'reject_videos', 'feature_videos']

    @admin.action(description='Approve selected videos')
    def approve_videos(self, request, queryset):
        from django.utils import timezone
        queryset.update(status=Video.Status.APPROVED, approved_at=timezone.now(), approved_by=request.user)

    @admin.action(description='Reject selected videos')
    def reject_videos(self, request, queryset):
        queryset.update(status=Video.Status.REJECTED)

    @admin.action(description='Mark as featured')
    def feature_videos(self, request, queryset):
        queryset.update(is_featured=True)


admin.site.register(SavedVideo)
admin.site.register(VideoView)
