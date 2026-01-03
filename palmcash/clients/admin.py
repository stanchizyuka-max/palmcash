from django.contrib import admin
from .models import BorrowerGroup, GroupMembership, OfficerAssignment, ClientAssignmentAuditLog


@admin.register(BorrowerGroup)
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


@admin.register(GroupMembership)
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


@admin.register(OfficerAssignment)
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


@admin.register(ClientAssignmentAuditLog)
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
