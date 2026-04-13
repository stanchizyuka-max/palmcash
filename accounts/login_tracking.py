"""
Login and session tracking for user activity monitoring
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class UserLoginSession(models.Model):
    """Track user login sessions"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='login_sessions'
    )
    
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    session_key = models.CharField(max_length=40, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['is_active', '-login_time']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"
    
    @property
    def session_duration(self):
        """Calculate session duration"""
        if self.logout_time:
            delta = self.logout_time - self.login_time
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        elif self.is_active:
            delta = timezone.now() - self.login_time
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            return f"{hours}h {minutes}m (active)"
        return "Unknown"


class UserActivityLog(models.Model):
    """Unified activity log for all user actions"""
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    
    ACTION_CHOICES = [
        # Authentication
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        
        # User Management
        ('user_create', 'Create User'),
        ('user_update', 'Update User'),
        ('user_delete', 'Delete User'),
        ('user_activate', 'Activate User'),
        ('user_deactivate', 'Deactivate User'),
        
        # Branch Management
        ('branch_create', 'Create Branch'),
        ('branch_update', 'Update Branch'),
        ('branch_delete', 'Delete Branch'),
        
        # Client Management
        ('client_create', 'Create Client'),
        ('client_update', 'Update Client'),
        ('client_transfer', 'Transfer Client'),
        ('client_assign', 'Assign Client'),
        
        # Group Management
        ('group_create', 'Create Group'),
        ('group_update', 'Update Group'),
        ('group_add_member', 'Add Group Member'),
        ('group_remove_member', 'Remove Group Member'),
        
        # Loan Management
        ('loan_apply', 'Apply for Loan'),
        ('loan_approve', 'Approve Loan'),
        ('loan_reject', 'Reject Loan'),
        ('loan_disburse', 'Disburse Loan'),
        ('loan_edit', 'Edit Loan'),
        ('loan_transfer', 'Transfer Loan'),
        
        # Payment Management
        ('payment_record', 'Record Payment'),
        ('payment_confirm', 'Confirm Payment'),
        ('payment_reject', 'Reject Payment'),
        ('collection_record', 'Record Collection'),
        ('default_collection', 'Default Collection'),
        
        # Security Deposit
        ('security_create', 'Create Security Deposit'),
        ('security_verify', 'Verify Security Deposit'),
        ('security_topup', 'Security Top-up'),
        ('security_return', 'Security Return'),
        
        # Document Management
        ('document_upload', 'Upload Document'),
        ('document_verify', 'Verify Document'),
        ('document_delete', 'Delete Document'),
        
        # Payroll
        ('payroll_generate', 'Generate Payroll'),
        ('payroll_payment', 'Process Payroll Payment'),
        ('salary_update', 'Update Salary'),
        
        # Reports & Views
        ('report_view', 'View Report'),
        ('report_export', 'Export Report'),
        ('dashboard_view', 'View Dashboard'),
        
        # Other
        ('other', 'Other Action'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=50, blank=True, help_text="Type of target (client, loan, branch, etc.)")
    target_id = models.CharField(max_length=100, blank=True, help_text="ID of the target object")
    target_name = models.CharField(max_length=255, blank=True, help_text="Name/description of target")
    
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Additional context
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['severity', '-timestamp']),
            models.Index(fields=['target_type', 'target_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp}"
