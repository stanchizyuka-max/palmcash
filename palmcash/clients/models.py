from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class BorrowerGroup(models.Model):
    """Groups for organizing borrowers"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
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
    
    # Branch and payment settings
    branch = models.CharField(
        max_length=100,
        blank=True,
        help_text='Branch location for this group'
    )
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
        return Loan.objects.filter(
            borrower__in=self.members.all(),
            status='active'
        ).count()
    
    def get_total_disbursed_amount(self):
        """Get total amount disbursed to group members"""
        from loans.models import Loan
        from django.db.models import Sum
        
        result = Loan.objects.filter(
            borrower__in=self.members.all(),
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
