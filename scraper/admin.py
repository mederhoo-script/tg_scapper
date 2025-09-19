from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Account, Group, ScrapingSession, ScrapedMember, 
    MessageTemplate, InviteLog, DMLog, Settings
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['phone', 'name', 'is_active', 'groups_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['phone', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    def groups_count(self, obj):
        return obj.groups.count()
    groups_count.short_description = 'Groups'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'account', 'identifier', 'group_type', 'member_count', 'is_active']
    list_filter = ['group_type', 'is_active', 'created_at']
    search_fields = ['name', 'identifier']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ScrapingSession)
class ScrapingSessionAdmin(admin.ModelAdmin):
    list_display = ['group', 'account', 'status', 'total_members_found', 'started_at', 'completed_at']
    list_filter = ['status', 'use_message_scraping', 'started_at']
    search_fields = ['group__name', 'account__phone']
    readonly_fields = ['started_at', 'completed_at', 'csv_file_path']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('group', 'account')


@admin.register(ScrapedMember)
class ScrapedMemberAdmin(admin.ModelAdmin):
    list_display = ['username_display', 'full_name', 'telegram_id', 'is_bot', 'is_active', 'session']
    list_filter = ['is_bot', 'is_verified', 'is_premium', 'is_active', 'scraped_at']
    search_fields = ['username', 'first_name', 'last_name', 'telegram_id']
    readonly_fields = ['scraped_at']
    
    def username_display(self, obj):
        if obj.username:
            return f"@{obj.username}"
        return "-"
    username_display.short_description = 'Username'
    
    def full_name(self, obj):
        name_parts = [obj.first_name, obj.last_name]
        return ' '.join(filter(None, name_parts)) or "-"
    full_name.short_description = 'Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session')


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'subject', 'content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(InviteLog)
class InviteLogAdmin(admin.ModelAdmin):
    list_display = ['member', 'target_group', 'account', 'status', 'attempted_at']
    list_filter = ['status', 'attempted_at']
    search_fields = ['member__username', 'member__first_name', 'target_group__name']
    readonly_fields = ['attempted_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('member', 'target_group', 'account')


@admin.register(DMLog)
class DMLogAdmin(admin.ModelAdmin):
    list_display = ['member', 'message_template', 'account', 'status', 'sent_at']
    list_filter = ['status', 'sent_at']
    search_fields = ['member__username', 'member__first_name', 'message_template__name']
    readonly_fields = ['sent_at', 'message_content']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('member', 'message_template', 'account')


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_display', 'description', 'updated_at']
    search_fields = ['key', 'value', 'description']
    readonly_fields = ['updated_at']
    
    def value_display(self, obj):
        if len(obj.value) > 50:
            return obj.value[:50] + "..."
        return obj.value
    value_display.short_description = 'Value'
