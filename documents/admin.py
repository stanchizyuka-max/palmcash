from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from .models import ClientDocument, ClientVerification

@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'document_type', 'status_display', 'uploaded_at', 'verified_by_name']
    list_filter = ['status', 'document_type', 'uploaded_at']
    search_fields = ['client__username', 'client__first_name', 'client__last_name']
    readonly_fields = ['uploaded_at', 'updated_at', 'file_size_mb', 'file_extension']
    list_per_page = 25
    
    fieldsets = (
        ('Document Information', {
            'fields': ('client', 'document_type', 'image')
        }),
        ('File Details', {
            'fields': ('file_size_mb', 'file_extension'),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': ('status', 'verified_by', 'verification_date', 'verification_notes')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_documents', 'reject_documents']
    
    def client_name(self, obj):
        """Display client name"""
        return obj.client.full_name
    client_name.short_description = 'Client'
    
    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': 'orange',
            'approved': 'green', 
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def verified_by_name(self, obj):
        """Display who verified the document"""
        if obj.verified_by:
            return obj.verified_by.full_name
        else:
            return "Pending"
    verified_by_name.short_description = 'Verified By'
    
    def approve_documents(self, request, queryset):
        """Bulk action to approve documents"""
        for doc in queryset:
            doc.approve(request.user, 'Approved via admin')
        self.message_user(request, f'{queryset.count()} documents approved.')
    approve_documents.short_description = "✅ Approve selected documents"
    
    def reject_documents(self, request, queryset):
        """Bulk action to reject documents"""
        for doc in queryset:
            doc.reject(request.user, 'Rejected via admin')
        self.message_user(request, f'{queryset.count()} documents rejected.')
    reject_documents.short_description = "❌ Reject selected documents"
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('client', 'verified_by')


@admin.register(ClientVerification)
class ClientVerificationAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'status_display', 'documents_status', 'verified_by_name', 'updated_at']
    list_filter = ['status', 'updated_at']
    search_fields = ['client__username', 'client__first_name', 'client__last_name']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('Client Information', {
            'fields': ('client',)
        }),
        ('Verification Status', {
            'fields': ('status', 'all_documents_approved')
        }),
        ('Document Upload Status', {
            'fields': ('nrc_front_uploaded', 'nrc_back_uploaded', 'selfie_uploaded')
        }),
        ('Verification Details', {
            'fields': ('verified_by', 'verification_date', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_all_documents', 'reject_all_documents', 'update_status']
    
    def client_name(self, obj):
        """Display client name"""
        return obj.client.full_name
    client_name.short_description = 'Client'
    
    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': 'gray',
            'documents_submitted': 'orange',
            'documents_rejected': 'red',
            'verified': 'green',
            'rejected': 'darkred',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def documents_status(self, obj):
        """Display document upload status"""
        docs = []
        if obj.nrc_front_uploaded:
            docs.append('✅ NRC-F')
        else:
            docs.append('⏳ NRC-F')
        if obj.nrc_back_uploaded:
            docs.append('✅ NRC-B')
        else:
            docs.append('⏳ NRC-B')
        if obj.selfie_uploaded:
            docs.append('✅ Selfie')
        else:
            docs.append('⏳ Selfie')
        return ' | '.join(docs)
    documents_status.short_description = 'Documents'
    
    def verified_by_name(self, obj):
        """Display who verified the client"""
        if obj.verified_by:
            return obj.verified_by.full_name
        else:
            return "Pending"
    verified_by_name.short_description = 'Verified By'
    
    def approve_all_documents(self, request, queryset):
        """Bulk action to approve all documents for selected clients"""
        for verification in queryset:
            verification.approve_all_documents(request.user)
        self.message_user(request, f'{queryset.count()} clients verified.')
    approve_all_documents.short_description = "✅ Approve all documents for selected clients"
    
    def reject_all_documents(self, request, queryset):
        """Bulk action to reject all documents for selected clients"""
        for verification in queryset:
            verification.reject_all_documents(request.user, 'Rejected via admin')
        self.message_user(request, f'{queryset.count()} clients rejected.')
    reject_all_documents.short_description = "❌ Reject all documents for selected clients"
    
    def update_status(self, request, queryset):
        """Bulk action to update verification status"""
        for verification in queryset:
            verification.update_status()
        self.message_user(request, f'Status updated for {queryset.count()} clients.')
    update_status.short_description = "🔄 Update verification status"
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('client', 'verified_by')
