from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

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
    assigned_officer = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_clients',
        limit_choices_to={'role': 'loan_officer'},
        help_text='Loan officer assigned to this client'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
