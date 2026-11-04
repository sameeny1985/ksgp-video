from django.contrib import admin
from .models import Campaign, CampaignPlacement, AdImpression, AdClick


class CampaignPlacementInline(admin.TabularInline):
    model = CampaignPlacement
    extra = 1


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'campaign_type', 'status', 'budget', 'spent', 'impressions', 'clicks', 'ctr', 'created_at')
    list_filter = ('status', 'campaign_type', 'pricing_model')
    search_fields = ('name', 'ad_title', 'owner__email')
    readonly_fields = ('uuid', 'spent', 'reserved', 'impressions', 'unique_impressions', 'clicks', 'unique_clicks', 'created_at', 'updated_at')
    inlines = [CampaignPlacementInline]
    actions = ['approve_campaigns', 'pause_campaigns', 'activate_campaigns']

    @admin.action(description='Approve selected campaigns')
    def approve_campaigns(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status=Campaign.Status.PENDING_REVIEW).update(
            status=Campaign.Status.APPROVED, reviewed_at=timezone.now(), reviewed_by=request.user
        )

    @admin.action(description='Pause selected campaigns')
    def pause_campaigns(self, request, queryset):
        queryset.filter(status=Campaign.Status.ACTIVE).update(status=Campaign.Status.PAUSED)

    @admin.action(description='Activate selected campaigns')
    def activate_campaigns(self, request, queryset):
        queryset.filter(status__in=[Campaign.Status.APPROVED, Campaign.Status.PAUSED, Campaign.Status.SCHEDULED]).update(
            status=Campaign.Status.ACTIVE
        )


@admin.register(AdImpression)
class AdImpressionAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'placement', 'is_valid', 'cost', 'created_at')
    list_filter = ('is_valid', 'placement', 'created_at')
    readonly_fields = [f.name for f in AdImpression._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False


@admin.register(AdClick)
class AdClickAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'placement', 'is_valid', 'is_unique', 'cost', 'created_at')
    list_filter = ('is_valid', 'is_unique', 'placement')
    readonly_fields = [f.name for f in AdClick._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
