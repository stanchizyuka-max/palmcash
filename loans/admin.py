from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import LoanType, Loan, LoanDocument

@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'interest_rate', 'min_amount', 'max_amount', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['application_number', 'borrower', 'principal_amount', 'status', 'application_date']
    list_filter = ['status', 'loan_type', 'application_date']
    search_fields = ['application_number', 'borrower__username', 'borrower__first_name', 'borrower__last_name']
    readonly_fields = ['application_number', 'total_amount', 'monthly_payment']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('borrower', 'loan_type', 'loan_officer', 'application_number')
        }),
        ('Loan Details', {
            'fields': ('principal_amount', 'interest_rate', 'term_months', 'monthly_payment', 'total_amount')
        }),
        ('Status', {
            'fields': ('status', 'approval_date', 'disbursement_date', 'maturity_date')
        }),
        ('Purpose & Collateral', {
            'fields': ('purpose', 'collateral_description', 'collateral_value')
        }),
        ('Financial Tracking', {
            'fields': ('amount_paid', 'balance_remaining')
        }),
        ('Notes', {
            'fields': ('approval_notes', 'rejection_reason')
        }),
    )


@admin.register(LoanDocument)
class LoanDocumentAdmin(admin.ModelAdmin):
    list_display = ['loan_info', 'document_type', 'original_filename', 'uploaded_by', 'uploaded_at', 'verification_status', 'verified_by']
    list_filter = ['document_type', 'is_verified', 'uploaded_at', 'loan__status']
    search_fields = ['loan__application_number', 'original_filename', 'uploaded_by__username', 'loan__borrower__username']
    readonly_fields = ['uploaded_at', 'verified_at', 'file_size_mb', 'file_extension', 'download_link']
    list_per_page = 25
    
    fieldsets = (
        ('Document Information', {
            'fields': ('loan', 'document_type', 'document_file', 'download_link', 'original_filename', 'description')
        }),
        ('Upload Details', {
            'fields': ('uploaded_by', 'uploaded_at', 'file_size_mb', 'file_extension')
        }),
        ('Verification (Admin Review)', {
            'fields': ('is_verified', 'verified_by', 'verified_at', 'verification_notes'),
            'classes': ('wide',),
            'description': 'Use this section to verify or reject the document after review.'
        }),
    )
    
    actions = ['mark_as_verified', 'mark_as_unverified', 'delete_selected_documents']
    
    def loan_info(self, obj):
        """Display loan information with status"""
        return f"{obj.loan.application_number} ({obj.loan.borrower.full_name}) - {obj.loan.get_status_display()}"
    loan_info.short_description = 'Loan Details'
    
    def verification_status(self, obj):
        """Display verification status with color coding"""
        if obj.is_verified:
            return f'✅ Verified by {obj.verified_by.full_name if obj.verified_by else "Unknown"}'
        else:
            return '⏳ Pending Review'
    verification_status.short_description = 'Status'
    
    def download_link(self, obj):
        """Provide download link for the document"""
        if obj.document_file:
            from django.urls import reverse
            from django.utils.html import format_html
            
            # Check if file exists on disk
            try:
                if obj.document_file.storage.exists(obj.document_file.name):
                    url = reverse('loans:download_document', args=[obj.pk])
                    return format_html('<a href="{}" class="button" target="_blank">📥 Download Document</a>', url)
                else:
                    return format_html('<span style="color: red;">❌ File Missing</span>')
            except:
                return format_html('<span style="color: red;">❌ File Error</span>')
        else:
            return format_html('<span style="color: orange;">⚠️ No File Uploaded</span>')
    download_link.short_description = 'Download'
    
    def mark_as_verified(self, request, queryset):
        """Bulk action to mark documents as verified"""
        from django.utils import timezone
        updated = queryset.update(
            is_verified=True,
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(request, f'{updated} documents marked as verified.')
    mark_as_verified.short_description = "✅ Mark selected documents as verified"
    
    def mark_as_unverified(self, request, queryset):
        """Bulk action to mark documents as unverified"""
        updated = queryset.update(
            is_verified=False,
            verified_by=None,
            verified_at=None
        )
        self.message_user(request, f'{updated} documents marked as unverified.')
    mark_as_unverified.short_description = "❌ Mark selected documents as unverified"
    
    def delete_selected_documents(self, request, queryset):
        """Bulk action to delete loan documents with confirmation"""
        deleted_count = 0
        for document in queryset:
            # Delete the file from storage if it exists
            if document.document_file:
                try:
                    document.document_file.delete(save=False)
                except Exception:
                    pass  # Continue even if file deletion fails
            
            document.delete()
            deleted_count += 1
        
        self.message_user(request, f'{deleted_count} loan document{"s" if deleted_count != 1 else ""} permanently deleted.')
    delete_selected_documents.short_description = "🗑️ Delete selected documents (PERMANENT)"
    
    def save_model(self, request, obj, form, change):
        """Auto-set verified_by and verified_at when marking as verified"""
        if obj.is_verified and not obj.verified_by:
            from django.utils import timezone
            obj.verified_by = request.user
            obj.verified_at = timezone.now()
        elif not obj.is_verified:
            obj.verified_by = None
            obj.verified_at = None
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.extend(['loan', 'document_file', 'uploaded_by'])
        return readonly
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('loan', 'loan__borrower', 'uploaded_by', 'verified_by')
    
    def changelist_view(self, request, extra_context=None):
        """Add document review statistics to the changelist"""
        extra_context = extra_context or {}
        
        # Add statistics
        total_docs = LoanDocument.objects.count()
        pending_docs = LoanDocument.objects.filter(is_verified=False).count()
        verified_docs = LoanDocument.objects.filter(is_verified=True).count()
        
        extra_context.update({
            'total_documents': total_docs,
            'pending_documents': pending_docs,
            'verified_documents': verified_docs,
            'verification_rate': round((verified_docs / total_docs * 100) if total_docs > 0 else 0, 1)
        })
        
        return super().changelist_view(request, extra_context=extra_context)
