from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone

class UserManager(DjangoUserManager):
    """Custom manager for User model"""
    
    def create_superuser(self, username, email, password, **extra_fields):
        """Create a superuser with admin role"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')  # Set role to admin
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    """Extended User model for LoanVista"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('loan_officer', 'Loan Officer'),
        ('borrower', 'Borrower'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='borrower')
    phone_number = PhoneNumberField(blank=True, null=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    national_id = models.CharField(max_length=50, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    # Employment Information
    employment_status = models.CharField(
        max_length=20,
        choices=[
            ('employed', 'Employed'),
            ('self_employed', 'Self Employed'),
            ('unemployed', 'Unemployed'),
            ('student', 'Student'),
            ('retired', 'Retired'),
        ],
        blank=True
    )
    employer_name = models.CharField(max_length=255, blank=True)
    employer_address = models.TextField(blank=True)
    employment_duration = models.IntegerField(blank=True, null=True, help_text='Employment duration in years')
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Business Information
    business_name = models.CharField(max_length=255, blank=True)
    business_address = models.TextField(blank=True)
    business_duration = models.IntegerField(blank=True, null=True, help_text='Business duration in years')
    
    # Residential Information
    residential_address = models.TextField(blank=True)
    residential_duration = models.IntegerField(blank=True, null=True, help_text='Residential duration in years')
    province = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    residential_area = models.CharField(max_length=255, blank=True)
    
    # Personal Information
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)
    
    # References
    reference1_name = models.CharField(max_length=255, blank=True)
    reference1_phone = models.CharField(max_length=20, blank=True)
    reference1_relationship = models.CharField(max_length=100, blank=True)
    reference2_name = models.CharField(max_length=255, blank=True)
    reference2_phone = models.CharField(max_length=20, blank=True)
    reference2_relationship = models.CharField(max_length=100, blank=True)

    # Guarantors
    guarantor1_name = models.CharField(max_length=255, blank=True)
    guarantor1_dob = models.DateField(null=True, blank=True)
    guarantor1_nrc = models.CharField(max_length=50, blank=True)
    guarantor1_phone = models.CharField(max_length=20, blank=True)
    guarantor1_address = models.TextField(blank=True)
    guarantor1_relationship = models.CharField(max_length=100, blank=True)

    guarantor2_name = models.CharField(max_length=255, blank=True)
    guarantor2_dob = models.DateField(null=True, blank=True)
    guarantor2_nrc = models.CharField(max_length=50, blank=True)
    guarantor2_phone = models.CharField(max_length=20, blank=True)
    guarantor2_address = models.TextField(blank=True)
    guarantor2_relationship = models.CharField(max_length=100, blank=True)
    
    assigned_officer = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_clients',
        limit_choices_to={'role': 'loan_officer'},
        help_text='Loan officer assigned to this client'
    )

    # Loan officer approval tracking
    is_approved = models.BooleanField(default=False, help_text='Has this loan officer been approved by a manager?')
    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_officers',
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def has_outstanding_loans(self):
        """Check if user has any outstanding loans"""
        if self.role != 'borrower':
            return False
        
        from loans.models import Loan
        return Loan.objects.filter(
            borrower=self,
            status__in=['active', 'approved', 'disbursed']
        ).exists()
    
    def get_outstanding_loans(self):
        """Get all outstanding loans for this borrower"""
        if self.role != 'borrower':
            return []
        
        from loans.models import Loan
        return Loan.objects.filter(
            borrower=self,
            status__in=['active', 'approved', 'disbursed']
        )
    
    def can_apply_for_loan(self):
        """Check if user can apply for a new loan"""
        if self.role != 'borrower':
            return False
        if self.has_outstanding_loans():
            return False
        # Check if user has verified documents (NRC front, NRC back, selfie)
        try:
            from documents.models import ClientVerification
            verification = ClientVerification.objects.get(client=self)
            return verification.can_apply_for_loan()
        except:
            # If documents app not available, allow application
            return True
    
    def has_verified_documents(self):
        """Check if user has at least one verified document"""
        if self.role != 'borrower':
            return True  # Non-borrowers don't need document verification
        
        try:
            from documents.models import Document
            return Document.objects.filter(
                user=self,
                status='approved'
            ).exists()
        except ImportError:
            return True  # If documents app not available, allow application
    
    def can_approve_loans(self):
        """Check if loan officer can approve loans (must manage at least 15 groups)"""
        if self.role != 'loan_officer':
            # Admins can always approve
            return self.role in ['admin', 'manager']
        
        try:
            from clients.models import OfficerAssignment, BorrowerGroup
            # Check if officer has at least 15 active groups
            active_groups_count = BorrowerGroup.objects.filter(
                assigned_officer=self,
                is_active=True
            ).count()
            return active_groups_count >= 15
        except ImportError:
            return False
    
    def get_active_groups_count(self):
        """Get count of active groups managed by this loan officer"""
        if self.role != 'loan_officer':
            return 0
        
        try:
            from clients.models import BorrowerGroup
            return BorrowerGroup.objects.filter(
                assigned_officer=self,
                is_active=True
            ).count()
        except ImportError:
            return 0
    
    class Meta:
        db_table = 'auth_user'

    def get_last_login_session(self):
        """Get the most recent login session"""
        return self.login_sessions.first()
    
    def get_active_session(self):
        """Get current active session"""
        return self.login_sessions.filter(is_active=True).first()
    
    def get_last_activity(self):
        """Get the most recent activity"""
        return self.activity_logs.first()
    
    def get_actions_today(self):
        """Count actions performed today"""
        from datetime import date
        return self.activity_logs.filter(timestamp__date=date.today()).count()
    
    def get_actions_this_week(self):
        """Count actions performed this week"""
        from datetime import date, timedelta
        week_ago = date.today() - timedelta(days=7)
        return self.activity_logs.filter(timestamp__date__gte=week_ago).count()
    
    def get_critical_actions_count(self):
        """Count critical actions"""
        return self.activity_logs.filter(severity='critical').count()
    
    @property
    def is_currently_active(self):
        """Check if user has an active session"""
        # Check Django sessions first
        from django.contrib.sessions.models import Session
        from django.utils import timezone as tz
        
        active_sessions = Session.objects.filter(expire_date__gte=tz.now())
        for session in active_sessions:
            data = session.get_decoded()
            user_id = data.get('_auth_user_id')
            if user_id and int(user_id) == self.id:
                return True
        
        # Fallback to our tracking
        session = self.get_active_session()
        if session:
            # Consider active if logged in within last 30 minutes
            from datetime import timedelta
            return (timezone.now() - session.login_time) < timedelta(minutes=30)
        return False



# Login and Activity Tracking Models
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
