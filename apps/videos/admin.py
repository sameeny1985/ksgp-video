from django.contrib import admin
from django.utils import timezone
from django.utils.text import slugify
import uuid
from .models import Video, SavedVideo, VideoView
from .youtube import fetch_youtube_meta


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'channel', 'owner', 'status', 'category', 'language', 'is_featured', 'is_sponsored', 'created_at')
    list_filter = ('status', 'is_featured', 'is_sponsored', 'language', 'category')
    search_fields = ('title', 'youtube_url', 'youtube_video_id', 'owner__email', 'channel__name')
    readonly_fields = ('uuid', 'youtube_video_id', 'title', 'thumbnail_url', 'created_at', 'updated_at')
    actions = ['approve_videos', 'reject_videos', 'feature_videos']
    fields = (
        'youtube_url',
        'title',
        'thumbnail_url',
        'slug',
        'channel',
        'owner',
        'description',
        'category',
        'language',
        'status',
        'is_featured',
        'is_sponsored',
        'youtube_video_id',
        'uuid',
        'created_at',
        'updated_at',
    )

    def save_model(self, request, obj, form, change):
        if obj.youtube_url:
            meta = fetch_youtube_meta(obj.youtube_url)
            if meta.get('video_id'):
                obj.youtube_video_id = meta['video_id']
            if meta.get('thumbnail_url'):
                obj.thumbnail_url = meta['thumbnail_url']
            if meta.get('title'):
                obj.title = meta['title'][:200]
            elif not obj.title:
                obj.title = f"YouTube video {obj.youtube_video_id or ''}".strip()
        if not obj.slug and obj.title:
            base = slugify(obj.title)[:180] or 'video'
            obj.slug = f'{base}-{uuid.uuid4().hex[:8]}'
        super().save_model(request, obj, form, change)

    @admin.action(description='Approve selected videos')
    def approve_videos(self, request, queryset):
        queryset.update(status=Video.Status.APPROVED, approved_at=timezone.now(), approved_by=request.user)

    @admin.action(description='Reject selected videos')
    def reject_videos(self, request, queryset):
        queryset.update(status=Video.Status.REJECTED)

    @admin.action(description='Mark as featured')
    def feature_videos(self, request, queryset):
        queryset.update(is_featured=True)


admin.site.register(SavedVideo)
admin.site.register(VideoView)
