from django.contrib import admin
from .models import (
    Branch, BorrowerGroup, GroupMembership, OfficerAssignment, ClientAssignmentAuditLog,
    OfficerTransferLog, ClientTransferLog, LoanApprovalQueue, ApprovalAuditLog,
    DisbursementAuditLog, CollectionAuditLog, AdminAuditLog
)


class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'location', 'manager', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'location', 'manager__first_name', 'manager__last_name']
    readonly_fields = ['created_at', 'updated_at', 'loan_officer_count', 'active_groups_count', 'total_clients_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'location', 'is_active')
        }),
        ('Management', {
            'fields': ('manager',)
        }),
        ('Contact Information', {
            'fields': ('phone', 'email')
        }),
        ('Statistics', {
            'fields': ('loan_officer_count', 'active_groups_count', 'total_clients_count'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class BorrowerGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'assigned_officer', 'member_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'assigned_officer']
    search_fields = ['name', 'description', 'assigned_officer__first_name', 'assigned_officer__last_name']
    readonly_fields = ['created_at', 'updated_at', 'member_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Assignment', {
            'fields': ('assigned_officer', 'max_members')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['borrower', 'group', 'joined_date', 'is_active', 'added_by']
    list_filter = ['is_active', 'joined_date', 'group']
    search_fields = ['borrower__first_name', 'borrower__last_name', 'group__name']
    readonly_fields = ['joined_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Membership', {
            'fields': ('borrower', 'group', 'is_active')
        }),
        ('Details', {
            'fields': ('notes', 'added_by')
        }),
        ('Dates', {
            'fields': ('joined_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class OfficerAssignmentAdmin(admin.ModelAdmin):
    list_display = ['officer', 'current_group_count', 'max_groups', 'current_client_count', 'max_clients', 'is_accepting_assignments']
    list_filter = ['is_accepting_assignments']
    search_fields = ['officer__first_name', 'officer__last_name', 'officer__email']
    readonly_fields = ['created_at', 'updated_at', 'current_group_count', 'current_client_count']
    
    fieldsets = (
        ('Officer', {
            'fields': ('officer',)
        }),
        ('Capacity Settings', {
            'fields': ('max_groups', 'max_clients', 'is_accepting_assignments')
        }),
        ('Current Workload', {
            'fields': ('current_group_count', 'current_client_count'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class ClientAssignmentAuditLogAdmin(admin.ModelAdmin):
    list_display = ['client', 'action', 'previous_officer', 'new_officer', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp', 'new_officer']
    search_fields = ['client__first_name', 'client__last_name', 'new_officer__first_name', 'new_officer__last_name']
    readonly_fields = ['timestamp', 'client', 'action', 'previous_officer', 'new_officer', 'performed_by', 'reason']
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('client', 'action', 'previous_officer', 'new_officer')
        }),
        ('Audit Information', {
            'fields': ('performed_by', 'reason', 'timestamp')
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation of audit logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs"""
        return False


class OfficerTransferLogAdmin(admin.ModelAdmin):
    list_display = ['officer', 'previous_branch', 'new_branch', 'performed_by', 'timestamp']
    list_filter = ['timestamp', 'performed_by']
    search_fields = ['officer__first_name', 'officer__last_name', 'previous_branch', 'new_branch']
    readonly_fields = ['timestamp', 'officer', 'previous_branch', 'new_branch', 'transferred_groups', 'reason', 'performed_by']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class ClientTransferLogAdmin(admin.ModelAdmin):
    list_display = ['client', 'previous_group', 'new_group', 'performed_by', 'timestamp']
    list_filter = ['timestamp', 'performed_by']
    search_fields = ['client__first_name', 'client__last_name', 'previous_group__name', 'new_group__name']
    readonly_fields = ['timestamp', 'client', 'previous_group', 'new_group', 'reason', 'performed_by']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class LoanApprovalQueueAdmin(admin.ModelAdmin):
    list_display = ['loan', 'status', 'submitted_date', 'decided_by', 'decision_date']
    list_filter = ['status', 'submitted_date', 'decision_date']
    search_fields = ['loan__id', 'loan__borrower__first_name', 'loan__borrower__last_name']
    readonly_fields = ['submitted_date', 'decision_date', 'loan']


class ApprovalAuditLogAdmin(admin.ModelAdmin):
    list_display = ['loan', 'action', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp', 'performed_by']
    search_fields = ['loan__id', 'performed_by__first_name', 'performed_by__last_name']
    readonly_fields = ['timestamp', 'loan', 'action', 'performed_by', 'reason', 'ip_address']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class DisbursementAuditLogAdmin(admin.ModelAdmin):
    list_display = ['loan', 'action', 'amount', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp', 'performed_by']
    search_fields = ['loan__id', 'performed_by__first_name', 'performed_by__last_name']
    readonly_fields = ['timestamp', 'loan', 'action', 'amount', 'performed_by', 'notes', 'ip_address']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class CollectionAuditLogAdmin(admin.ModelAdmin):
    list_display = ['loan', 'action', 'amount_collected', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp', 'performed_by']
    search_fields = ['loan__id', 'performed_by__first_name', 'performed_by__last_name']
    readonly_fields = ['timestamp', 'loan', 'action', 'amount_expected', 'amount_collected', 'performed_by', 'notes', 'ip_address']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ['admin_user', 'action', 'affected_user', 'timestamp']
    list_filter = ['action', 'timestamp', 'admin_user']
    search_fields = ['admin_user__first_name', 'admin_user__last_name', 'affected_user__first_name', 'affected_user__last_name']
    readonly_fields = ['timestamp', 'admin_user', 'action', 'affected_user', 'affected_branch', 'affected_group', 'description', 'old_value', 'new_value', 'ip_address']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# Register models with custom admin site
def register_admin_models():
    """Register all models with the custom admin site"""
    from common.admin import custom_admin_site
    custom_admin_site.register(Branch, BranchAdmin)
    custom_admin_site.register(BorrowerGroup, BorrowerGroupAdmin)
    custom_admin_site.register(GroupMembership, GroupMembershipAdmin)
    custom_admin_site.register(OfficerAssignment, OfficerAssignmentAdmin)
    custom_admin_site.register(ClientAssignmentAuditLog, ClientAssignmentAuditLogAdmin)
    custom_admin_site.register(OfficerTransferLog, OfficerTransferLogAdmin)
    custom_admin_site.register(ClientTransferLog, ClientTransferLogAdmin)
    custom_admin_site.register(LoanApprovalQueue, LoanApprovalQueueAdmin)
    custom_admin_site.register(ApprovalAuditLog, ApprovalAuditLogAdmin)
    custom_admin_site.register(DisbursementAuditLog, DisbursementAuditLogAdmin)
    custom_admin_site.register(CollectionAuditLog, CollectionAuditLogAdmin)
    custom_admin_site.register(AdminAuditLog, AdminAuditLogAdmin)


# Call registration function
register_admin_models()
