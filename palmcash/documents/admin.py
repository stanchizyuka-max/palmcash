from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from .models import DocumentType, Document

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_required', 'max_file_size_mb', 'allowed_extensions', 'is_active']
    list_filter = ['is_required', 'is_active']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Requirements', {
            'fields': ('is_required', 'max_file_size_mb', 'allowed_extensions')
        }),
    )

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['document_info', 'user_info', 'document_type', 'status_display', 'uploaded_at', 'review_status', 'download_link']
    list_filter = ['status', 'document_type', 'uploaded_at', 'user__role']
    search_fields = ['title', 'user__username', 'user__first_name', 'user__last_name', 'document_number']
    readonly_fields = ['uploaded_at', 'updated_at', 'file_size', 'original_filename', 'file_extension']
    list_per_page = 25
    
    fieldsets = (
        ('Document Information', {
            'fields': ('user', 'loan', 'document_type', 'title', 'description')
        }),
        ('File Details', {
            'fields': ('file', 'original_filename', 'file_size', 'file_extension')
        }),
        ('Document Details', {
            'fields': ('document_number', 'issue_date', 'expiry_date')
        }),
        ('Review & Status', {
            'fields': ('status', 'reviewed_by', 'review_date', 'review_notes'),
            'classes': ('wide',),
            'description': 'Use this section to review and approve/reject the document.'
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_documents', 'reject_documents', 'mark_pending_review', 'delete_selected_documents']
    
    def document_info(self, obj):
        """Display document title with type"""
        return f"{obj.title} ({obj.document_type.name})"
    document_info.short_description = 'Document'
    
    def user_info(self, obj):
        """Display user information"""
        return f"{obj.user.full_name} ({obj.user.username})"
    user_info.short_description = 'User'
    
    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': 'orange',
            'approved': 'green', 
            'rejected': 'red',
            'expired': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def review_status(self, obj):
        """Display review information"""
        if obj.reviewed_by:
            return f"✅ {obj.reviewed_by.full_name}"
        else:
            return "⏳ Pending Review"
    review_status.short_description = 'Reviewed By'
    
    def download_link(self, obj):
        """Provide download link for the document"""
        if obj.file:
            try:
                if obj.file.storage.exists(obj.file.name):
                    # Create a direct download URL
                    return format_html(
                        '<a href="{}" class="button" target="_blank" download>📥 Download</a>',
                        obj.file.url
                    )
                else:
                    return format_html('<span style="color: red;">❌ File Missing</span>')
            except:
                return format_html('<span style="color: red;">❌ File Error</span>')
        else:
            return format_html('<span style="color: orange;">⚠️ No File</span>')
    download_link.short_description = 'Download'
    
    def approve_documents(self, request, queryset):
        """Bulk action to approve documents"""
        updated = queryset.update(
            status='approved',
            reviewed_by=request.user,
            review_date=timezone.now()
        )
        self.message_user(request, f'{updated} documents approved.')
    approve_documents.short_description = "✅ Approve selected documents"
    
    def reject_documents(self, request, queryset):
        """Bulk action to reject documents"""
        updated = queryset.update(
            status='rejected',
            reviewed_by=request.user,
            review_date=timezone.now()
        )
        self.message_user(request, f'{updated} documents rejected.')
    reject_documents.short_description = "❌ Reject selected documents"
    
    def mark_pending_review(self, request, queryset):
        """Bulk action to mark documents as pending review"""
        updated = queryset.update(
            status='pending',
            reviewed_by=None,
            review_date=None
        )
        self.message_user(request, f'{updated} documents marked as pending review.')
    mark_pending_review.short_description = "⏳ Mark as pending review"
    
    def delete_selected_documents(self, request, queryset):
        """Bulk action to delete documents with confirmation"""
        deleted_count = 0
        for document in queryset:
            # Delete the file from storage if it exists
            if document.file:
                try:
                    document.file.delete(save=False)
                except Exception:
                    pass  # Continue even if file deletion fails
            
            document.delete()
            deleted_count += 1
        
        self.message_user(request, f'{deleted_count} document{"s" if deleted_count != 1 else ""} permanently deleted.')
    delete_selected_documents.short_description = "🗑️ Delete selected documents (PERMANENT)"
    
    def save_model(self, request, obj, form, change):
        """Auto-set reviewed_by and review_date when status changes"""
        if change and 'status' in form.changed_data:
            if obj.status in ['approved', 'rejected'] and not obj.reviewed_by:
                obj.reviewed_by = request.user
                obj.review_date = timezone.now()
            elif obj.status == 'pending':
                obj.reviewed_by = None
                obj.review_date = None
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('user', 'document_type', 'reviewed_by', 'loan')
    
    def changelist_view(self, request, extra_context=None):
        """Add document review statistics to the changelist"""
        extra_context = extra_context or {}
        
        # Add statistics
        total_docs = Document.objects.count()
        pending_docs = Document.objects.filter(status='pending').count()
        approved_docs = Document.objects.filter(status='approved').count()
        rejected_docs = Document.objects.filter(status='rejected').count()
        
        extra_context.update({
            'total_documents': total_docs,
            'pending_documents': pending_docs,
            'approved_documents': approved_docs,
            'rejected_documents': rejected_docs,
            'approval_rate': round((approved_docs / total_docs * 100) if total_docs > 0 else 0, 1)
        })
        
        return super().changelist_view(request, extra_context=extra_context)