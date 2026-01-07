from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Branch(models.Model):
    """Represents a branch location"""
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Branch code (e.g., MB, SB1)")
    location = models.CharField(max_length=200, help_text="Physical location/address")
    manager = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_branch',
        limit_choices_to={'role': 'manager'},
        help_text='Branch manager'
    )
    
    # Contact information
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def loan_officer_count(self):
        """Get number of loan officers in this branch"""
        return OfficerAssignment.objects.filter(
            branch=self,
            officer__is_active=True
        ).count()
    
    @property
    def active_groups_count(self):
        """Get number of active groups in this branch"""
        return self.groups.filter(is_active=True).count()
    
    @property
    def total_clients_count(self):
        """Get total number of clients in this branch"""
        from django.db.models import Count
        return self.groups.aggregate(
            total=Count('members', distinct=True)
        )['total'] or 0


class BorrowerGroup(models.Model):
    """Groups for organizing borrowers"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Branch assignment
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='groups',
        help_text='Branch this group belongs to'
    )
    
    # Loan officer assigned to manage this group
    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_groups',
        limit_choices_to={'role': 'loan_officer'},
        help_text='Loan officer responsible for this group'
    )
    
    # Payment settings
    payment_day = models.CharField(
        max_length=20,
        blank=True,
        help_text='Day of payment (e.g., Monday, Tuesday for weekly; or specific day number for daily)'
    )
    
    # Group settings
    max_members = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='Maximum number of members (leave blank for unlimited)'
    )
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Borrower Group'
        verbose_name_plural = 'Borrower Groups'
        permissions = [
            ('can_create_group', 'Can create borrower groups'),
        ]
    
    def __str__(self):
        officer_name = self.assigned_officer.full_name if self.assigned_officer else 'Unassigned'
        return f"{self.name} (Officer: {officer_name})"
    
    @property
    def member_count(self):
        """Get current number of members"""
        return self.members.count()
    
    @property
    def active_member_count(self):
        """Get number of active members"""
        return self.members.filter(is_active=True).count()
    
    @property
    def is_full(self):
        """Check if group has reached max capacity"""
        if not self.max_members:
            return False
        return self.member_count >= self.max_members
    
    def can_add_member(self):
        """Check if new members can be added"""
        return self.is_active and not self.is_full
    
    def get_active_loans_count(self):
        """Get count of active loans for group members"""
        from loans.models import Loan
        # Get borrowers from group memberships
        borrowers = self.members.filter(is_active=True).values_list('borrower', flat=True)
        return Loan.objects.filter(
            borrower__in=borrowers,
            status='active'
        ).count()
    
    def get_total_disbursed_amount(self):
        """Get total amount disbursed to group members"""
        from loans.models import Loan
        from django.db.models import Sum
        
        # Get borrowers from group memberships
        borrowers = self.members.filter(is_active=True).values_list('borrower', flat=True)
        result = Loan.objects.filter(
            borrower__in=borrowers,
            status__in=['active', 'completed']
        ).aggregate(total=Sum('principal_amount'))
        
        return result['total'] or 0


class GroupMembership(models.Model):
    """Track borrower membership in groups"""
    
    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_memberships',
        limit_choices_to={'role': 'borrower'}
    )
    group = models.ForeignKey(
        BorrowerGroup,
        on_delete=models.CASCADE,
        related_name='members'
    )
    
    # Membership details
    joined_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, help_text='Notes about this membership')
    
    # Who added this member
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_memberships'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['borrower', 'group']
        ordering = ['-joined_date']
        verbose_name = 'Group Membership'
        verbose_name_plural = 'Group Memberships'
    
    def __str__(self):
        return f"{self.borrower.full_name} in {self.group.name}"
    
    def deactivate(self):
        """Deactivate this membership"""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
    
    def activate(self):
        """Activate this membership"""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


class OfficerAssignment(models.Model):
    """Track loan officer assignments and workload"""
    
    officer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='officer_assignment',
        limit_choices_to={'role': 'loan_officer'}
    )
    
    # Branch assignment
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_officers',
        help_text='Branch where this loan officer is assigned'
    )
    
    # Workload settings
    max_groups = models.IntegerField(
        default=15,
        validators=[MinValueValidator(15)],
        help_text='Maximum number of groups this officer can manage (minimum 15)'
    )
    max_clients = models.IntegerField(
        default=50,
        validators=[MinValueValidator(1)],
        help_text='Maximum number of individual clients this officer can handle'
    )
    
    # Status
    is_accepting_assignments = models.BooleanField(
        default=True,
        help_text='Is this officer accepting new assignments?'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Officer Assignment'
        verbose_name_plural = 'Officer Assignments'
    
    def __str__(self):
        return f"{self.officer.full_name} - Assignment Settings"
    
    @property
    def current_group_count(self):
        """Get number of groups currently assigned"""
        return self.officer.managed_groups.filter(is_active=True).count()
    
    @property
    def current_client_count(self):
        """Get number of clients currently assigned"""
        return self.officer.assigned_clients.filter(role='borrower', is_active=True).count()
    
    @property
    def is_at_group_capacity(self):
        """Check if officer has reached max groups"""
        return self.current_group_count >= self.max_groups
    
    @property
    def is_at_client_capacity(self):
        """Check if officer has reached max clients"""
        return self.current_client_count >= self.max_clients
    
    @property
    def can_accept_new_group(self):
        """Check if officer can accept a new group"""
        return self.is_accepting_assignments and not self.is_at_group_capacity
    
    @property
    def can_accept_new_client(self):
        """Check if officer can accept a new client"""
        return self.is_accepting_assignments and not self.is_at_client_capacity
    
    def get_workload_percentage(self):
        """Calculate workload as percentage of capacity"""
        group_pct = (self.current_group_count / self.max_groups) * 100
        client_pct = (self.current_client_count / self.max_clients) * 100
        return max(group_pct, client_pct)
    
    def meets_minimum_groups(self):
        """Check if officer manages at least 15 active groups"""
        return self.current_group_count >= 15
    
    def can_approve_loans(self):
        """Check if officer can approve loans (must manage at least 15 groups)"""
        return self.meets_minimum_groups()


class ClientAssignmentAuditLog(models.Model):
    """Track client assignment changes for audit purposes"""
    
    ACTION_CHOICES = [
        ('assign', 'Assign'),
        ('unassign', 'Unassign'),
        ('reassign', 'Reassign'),
    ]
    
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignment_audit_logs',
        limit_choices_to={'role': 'borrower'},
        help_text='The borrower client being assigned'
    )
    
    previous_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='previous_assignments',
        limit_choices_to={'role': 'loan_officer'},
        help_text='The previous loan officer (if reassigning)'
    )
    
    new_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='new_assignments',
        limit_choices_to={'role': 'loan_officer'},
        help_text='The new loan officer (null if unassigning)'
    )
    
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text='Type of assignment action'
    )
    
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='performed_assignments',
        help_text='The user who performed this action'
    )
    
    reason = models.TextField(
        blank=True,
        help_text='Optional reason for the assignment change'
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When this assignment change occurred'
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Client Assignment Audit Log'
        verbose_name_plural = 'Client Assignment Audit Logs'
        indexes = [
            models.Index(fields=['client', '-timestamp']),
            models.Index(fields=['new_officer', '-timestamp']),
        ]
    
    def __str__(self):
        if self.action == 'unassign':
            return f"{self.client.full_name} unassigned from {self.previous_officer.full_name} on {self.timestamp.date()}"
        elif self.action == 'reassign':
            return f"{self.client.full_name} reassigned from {self.previous_officer.full_name} to {self.new_officer.full_name} on {self.timestamp.date()}"
        else:
            return f"{self.client.full_name} assigned to {self.new_officer.full_name} on {self.timestamp.date()}"


class AdminAuditLog(models.Model):
    """Track all admin actions for audit purposes"""
    
    ACTION_CHOICES = [
        ('branch_create', 'Create Branch'),
        ('branch_update', 'Update Branch'),
        ('branch_delete', 'Delete Branch'),
        ('officer_transfer', 'Transfer Officer'),
        ('officer_update', 'Update Officer'),
        ('group_transfer', 'Transfer Group'),
        ('client_transfer', 'Transfer Client'),
        ('loan_approve', 'Approve Loan'),
        ('loan_reject', 'Reject Loan'),
        ('override_assignment', 'Override Assignment'),
        ('other', 'Other'),
    ]
    
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_actions',
        limit_choices_to={'role': 'admin'},
        help_text='Admin who performed the action'
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text='Type of action performed'
    )
    
    # Affected entities
    affected_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_affected_actions',
        help_text='User affected by this action'
    )
    
    affected_branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_actions',
        help_text='Branch affected by this action'
    )
    
    affected_group = models.ForeignKey(
        BorrowerGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_actions',
        help_text='Group affected by this action'
    )
    
    # Details
    description = models.TextField(
        help_text='Description of the action'
    )
    
    old_value = models.TextField(
        blank=True,
        help_text='Previous value (if applicable)'
    )
    
    new_value = models.TextField(
        blank=True,
        help_text='New value (if applicable)'
    )
    
    # Timestamp
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When this action occurred'
    )
    
    # IP and user agent for security
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the admin'
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Admin Audit Log'
        verbose_name_plural = 'Admin Audit Logs'
        indexes = [
            models.Index(fields=['admin_user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['affected_user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} by {self.admin_user.username} on {self.timestamp.date()}"



class OfficerTransferLog(models.Model):
    """Track officer transfers between branches"""
    
    officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='officer_transfers',
        help_text='Officer being transferred'
    )
    previous_branch = models.CharField(
        max_length=100,
        help_text='Previous branch name'
    )
    new_branch = models.CharField(
        max_length=100,
        help_text='New branch name'
    )
    transferred_groups = models.JSONField(
        default=list,
        help_text='List of group IDs transferred'
    )
    reason = models.TextField(
        help_text='Reason for transfer'
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='performed_officer_transfers',
        help_text='Admin who performed transfer'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When transfer occurred'
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Officer Transfer Log'
        verbose_name_plural = 'Officer Transfer Logs'
        indexes = [
            models.Index(fields=['officer', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.officer.full_name} transferred from {self.previous_branch} to {self.new_branch} on {self.timestamp.date()}"


class ClientTransferLog(models.Model):
    """Track client transfers between groups"""
    
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_transfers',
        limit_choices_to={'role': 'borrower'},
        help_text='Client being transferred'
    )
    previous_group = models.ForeignKey(
        BorrowerGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='previous_transfers',
        help_text='Previous group'
    )
    new_group = models.ForeignKey(
        BorrowerGroup,
        on_delete=models.SET_NULL,
        null=True,
        related_name='new_transfers',
        help_text='New group'
    )
    reason = models.TextField(
        help_text='Reason for transfer'
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='performed_client_transfers',
        help_text='Admin who performed transfer'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When transfer occurred'
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Client Transfer Log'
        verbose_name_plural = 'Client Transfer Logs'
        indexes = [
            models.Index(fields=['client', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
        ]
    
    def __str__(self):
        prev_group = self.previous_group.name if self.previous_group else 'Unknown'
        return f"{self.client.full_name} transferred from {prev_group} to {self.new_group.name} on {self.timestamp.date()}"


class LoanApprovalQueue(models.Model):
    """Track loans pending admin approval"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    loan = models.OneToOneField(
        'loans.Loan',
        on_delete=models.CASCADE,
        related_name='approval_queue',
        help_text='Loan awaiting approval'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Approval status'
    )
    submitted_date = models.DateTimeField(
        auto_now_add=True,
        help_text='When loan was submitted for approval'
    )
    decision_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When decision was made'
    )
    decision_reason = models.TextField(
        blank=True,
        help_text='Reason for approval/rejection'
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loan_decisions',
        help_text='Admin who made decision'
    )
    
    class Meta:
        ordering = ['-submitted_date']
        verbose_name = 'Loan Approval Queue'
        verbose_name_plural = 'Loan Approval Queues'
        indexes = [
            models.Index(fields=['status', '-submitted_date']),
            models.Index(fields=['decided_by', '-decision_date']),
        ]
    
    def __str__(self):
        return f"Loan {self.loan.id} - {self.get_status_display()} (K{self.loan.principal_amount})"


class ApprovalAuditLog(models.Model):
    """Track approval actions for audit trail"""
    
    ACTION_CHOICES = [
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.CASCADE,
        related_name='approval_audits',
        help_text='Loan being approved'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text='Approval action'
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approval_actions',
        help_text='User who performed action'
    )
    reason = models.TextField(
        blank=True,
        help_text='Reason for action'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When action occurred'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of user'
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Approval Audit Log'
        verbose_name_plural = 'Approval Audit Logs'
        indexes = [
            models.Index(fields=['loan', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Loan {self.loan.id} - {self.get_action_display()} by {self.performed_by.username} on {self.timestamp.date()}"


class DisbursementAuditLog(models.Model):
    """Track disbursement actions for audit trail"""
    
    ACTION_CHOICES = [
        ('initiated', 'Initiated'),
        ('processed', 'Processed'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.CASCADE,
        related_name='disbursement_audits',
        help_text='Loan being disbursed'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text='Disbursement action'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Amount disbursed'
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='disbursement_actions',
        help_text='User who performed action'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When action occurred'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of user'
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Disbursement Audit Log'
        verbose_name_plural = 'Disbursement Audit Logs'
        indexes = [
            models.Index(fields=['loan', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Loan {self.loan.id} - {self.get_action_display()} K{self.amount} on {self.timestamp.date()}"


class CollectionAuditLog(models.Model):
    """Track collection actions for audit trail"""
    
    ACTION_CHOICES = [
        ('collected', 'Collected'),
        ('partial', 'Partial'),
        ('missed', 'Missed'),
        ('default', 'Default'),
    ]
    
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.CASCADE,
        related_name='collection_audits',
        help_text='Loan with collection'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text='Collection action'
    )
    amount_expected = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Expected collection amount'
    )
    amount_collected = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Actual collection amount'
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='collection_actions',
        help_text='User who performed action'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When action occurred'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of user'
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Collection Audit Log'
        verbose_name_plural = 'Collection Audit Logs'
        indexes = [
            models.Index(fields=['loan', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Loan {self.loan.id} - {self.get_action_display()} K{self.amount_collected} on {self.timestamp.date()}"
