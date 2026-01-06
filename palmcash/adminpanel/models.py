from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class OfficerTransferLog(models.Model):
    """Track officer transfers between branches"""
    
    officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transfer_logs'
    )
    previous_branch = models.CharField(max_length=100)
    new_branch = models.CharField(max_length=100)
    transferred_groups = models.JSONField(
        default=list,
        help_text='List of group IDs transferred'
    )
    reason = models.TextField()
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='officer_transfers_performed'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Officer Transfer Log'
        verbose_name_plural = 'Officer Transfer Logs'
        indexes = [
            models.Index(fields=['officer', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.officer.full_name} transferred from {self.previous_branch} to {self.new_branch}"


class ClientTransferLog(models.Model):
    """Track client transfers between groups"""
    
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_transfer_logs'
    )
    previous_group_id = models.IntegerField(null=True, blank=True)
    previous_group_name = models.CharField(max_length=100, blank=True)
    new_group_id = models.IntegerField(null=True, blank=True)
    new_group_name = models.CharField(max_length=100, blank=True)
    reason = models.TextField()
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='client_transfers_performed'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Client Transfer Log'
        verbose_name_plural = 'Client Transfer Logs'
        indexes = [
            models.Index(fields=['client', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.client.full_name} transferred from {self.previous_group_name} to {self.new_group_name}"


class ApprovalAuditLog(models.Model):
    """Track approval actions for loans"""
    
    ACTION_CHOICES = [
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.CASCADE,
        related_name='approval_audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approval_audits'
    )
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Approval Audit Log'
        verbose_name_plural = 'Approval Audit Logs'
        indexes = [
            models.Index(fields=['loan', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.loan.application_number} by {self.performed_by.full_name}"


class DisbursementAuditLog(models.Model):
    """Track disbursement actions"""
    
    ACTION_CHOICES = [
        ('initiated', 'Initiated'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.CASCADE,
        related_name='disbursement_audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='disbursement_audits'
    )
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Disbursement Audit Log'
        verbose_name_plural = 'Disbursement Audit Logs'
        indexes = [
            models.Index(fields=['loan', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.loan.application_number} ({self.amount})"


class CollectionAuditLog(models.Model):
    """Track collection actions"""
    
    ACTION_CHOICES = [
        ('payment_received', 'Payment Received'),
        ('payment_recorded', 'Payment Recorded'),
        ('default_marked', 'Default Marked'),
        ('collection_attempt', 'Collection Attempt'),
    ]
    
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.CASCADE,
        related_name='collection_audit_logs'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='collection_audits'
    )
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Collection Audit Log'
        verbose_name_plural = 'Collection Audit Logs'
        indexes = [
            models.Index(fields=['loan', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.loan.application_number}"


class AdminAuditLog(models.Model):
    """Track all admin actions for compliance"""
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('transfer', 'Transfer'),
        ('override', 'Override'),
        ('other', 'Other'),
    ]
    
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    resource_type = models.CharField(
        max_length=50,
        help_text='Type of resource affected (e.g., Branch, Officer, Client, Loan)'
    )
    resource_id = models.IntegerField(null=True, blank=True)
    resource_name = models.CharField(max_length=255, blank=True)
    
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_audit_logs'
    )
    
    # Change tracking
    previous_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    # Additional info
    reason = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Admin Audit Log'
        verbose_name_plural = 'Admin Audit Logs'
        indexes = [
            models.Index(fields=['performed_by', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['resource_type', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_type_display()} {self.resource_type} by {self.performed_by.full_name if self.performed_by else 'Unknown'}"
