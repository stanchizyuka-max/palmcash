from django.contrib import admin
from .models import NotificationTemplate, Notification

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'notification_type', 'channel', 'is_active']
    list_filter = ['channel', 'is_active']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'template', 'status', 'scheduled_at']
    list_filter = ['status', 'channel', 'scheduled_at']