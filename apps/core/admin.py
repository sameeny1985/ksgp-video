from django.contrib import admin
from .models import Category, Tag, SystemSetting, Language, PageContent, AuditLog, ChainBlock


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_featured', 'parent')
    list_editable = ('order', 'is_featured')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'usage_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value_type', 'is_public', 'updated_at')
    list_filter = ('value_type', 'is_public')
    search_fields = ('key', 'description')


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'native_name', 'is_rtl', 'is_active', 'order')
    list_editable = ('is_active', 'order')


@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'model_name', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('action', 'details')
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(ChainBlock)
class ChainBlockAdmin(admin.ModelAdmin):
    list_display = ('index', 'event_type', 'actor_email', 'object_type', 'object_id', 'block_hash_short', 'timestamp')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('actor_email', 'object_id', 'block_hash', 'event_type')
    readonly_fields = [f.name for f in ChainBlock._meta.fields]
    ordering = ('-index',)

    def block_hash_short(self, obj):
        return obj.block_hash[:16] + '…'
    block_hash_short.short_description = 'Hash'

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
