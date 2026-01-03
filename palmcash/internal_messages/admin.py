from django.contrib import admin
from .models import Message, MessageThread, ThreadMessage


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['subject', 'body', 'sender__email', 'recipient__email']
    readonly_fields = ['created_at', 'updated_at', 'read_at']


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ['subject', 'created_by', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['subject']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ThreadMessage)
class ThreadMessageAdmin(admin.ModelAdmin):
    list_display = ['thread', 'sender', 'created_at']
    list_filter = ['created_at']
    search_fields = ['body', 'sender__email']
    readonly_fields = ['created_at']
