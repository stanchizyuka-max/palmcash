from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import datetime, timedelta
import os

class LoanType(models.Model):
    """Different types of loans offered - Daily and Weekly repayment only"""
    
    REPAYMENT_FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=45.00, help_text="Interest rate (default 45%)")
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Repayment frequency
    repayment_frequency = models.CharField(
        max_length=10, 
        choices=REPAYMENT_FREQUENCY_CHOICES, 
        default='weekly',
        help_text="Repayment frequency for this loan type"
    )
    
    # Term limits based on frequency
    min_term_days = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Minimum term in days (for daily loans)",
        validators=[MinValueValidator(1)]
    )
    max_term_days = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Maximum term in days (for daily loans)",
        validators=[MinValueValidator(1)]
    )
    min_term_weeks = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Minimum term in weeks (for weekly loans)",
        validators=[MinValueValidator(1)]
    )
    max_term_weeks = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Maximum term in weeks (for weekly loans)",
        validators=[MinValueValidator(1)]
    )
    
    # Legacy monthly fields (deprecated)
    max_term_months = models.IntegerField(
        null=True,
        blank=True,
        help_text="DEPRECATED: No longer used"
    )
    min_term_months = models.IntegerField(
        null=True,
        blank=True,
        help_text="DEPRECATED: No longer used"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_repayment_frequency_display()})"
    
    def get_term_display(self):
        """Get human-readable term range"""
        if self.repayment_frequency == 'daily' and self.min_term_days and self.max_term_days:
            return f"{self.min_term_days}-{self.max_term_days} days"
        elif self.repayment_frequency == 'weekly' and self.min_term_weeks and self.max_term_weeks:
            return f"{self.min_term_weeks}-{self.max_term_weeks} weeks"
        return "Term not configured"

class Loan(models.Model):
    """Main loan model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
    ]
    
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    loan_officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_loans')
    
    # Loan Details
    application_number = models.CharField(max_length=20, unique=True)
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=45.00, help_text="Interest rate (default 45%)")
    
    # Repayment frequency and terms
    repayment_frequency = models.CharField(
        max_length=10, 
        choices=[('daily', 'Daily'), ('weekly', 'Weekly')],
        default='weekly',
        help_text="Repayment frequency: daily or weekly"
    )
    term_days = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Loan term in days (for daily repayment)",
        validators=[MinValueValidator(1)]
    )
    term_weeks = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Loan term in weeks (for weekly repayment)",
        validators=[MinValueValidator(1)]
    )
    payment_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Daily or weekly payment amount"
    )
    
    # Legacy monthly fields (deprecated - kept for data migration only)
    term_months = models.IntegerField(
        null=True,
        blank=True,
        help_text="DEPRECATED: Use term_days or term_weeks instead"
    )
    monthly_payment = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="DEPRECATED: Use payment_amount instead"
    )
    
    # Status and Dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    application_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    disbursement_date = models.DateTimeField(null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)
    
    # Purpose and Collateral
    purpose = models.TextField()
    collateral_description = models.TextField(blank=True)
    collateral_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Financial Details
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_remaining = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Upfront Payment (10% requirement)
    upfront_payment_required = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="10% of principal amount")
    upfront_payment_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Amount paid upfront")
    upfront_payment_date = models.DateTimeField(null=True, blank=True, help_text="Date when upfront payment was made")
    upfront_payment_verified = models.BooleanField(default=False, help_text="Has the upfront payment been verified?")
    
    # Manager Approval Tracking
    manager_approval_required = models.BooleanField(default=False, help_text="Whether manager approval is needed")
    manager_approved_date = models.DateTimeField(null=True, blank=True, help_text="Date when manager approved the loan")
    
    # Notes
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Loan {self.application_number} - {self.borrower.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            # Generate unique application number
            last_loan = Loan.objects.order_by('-id').first()
            if last_loan:
                last_number = int(last_loan.application_number.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.application_number = f"LV-{new_number:06d}"
        
        # Calculate upfront payment (10% of principal)
        if self.principal_amount and not self.upfront_payment_required:
            from decimal import Decimal
            principal = Decimal(str(self.principal_amount))
            self.upfront_payment_required = principal * Decimal('0.10')
        
        # Calculate payment amount and total based on frequency
        if self.principal_amount and self.interest_rate:
            # Ensure we're working with Decimals
            from decimal import Decimal
            principal = Decimal(str(self.principal_amount))
            interest_rate = Decimal(str(self.interest_rate))
            
            # Calculate total with interest
            interest_amount = principal * (interest_rate / Decimal('100'))
            self.total_amount = principal + interest_amount
            
        # Calculate payment amount based on frequency
            if self.repayment_frequency == 'daily' and self.term_days:
                self.payment_amount = self.total_amount / Decimal(str(self.term_days))
            elif self.repayment_frequency == 'weekly' and self.term_weeks:
                self.payment_amount = self.total_amount / Decimal(str(self.term_weeks))
            
        if self.total_amount and not self.balance_remaining:
            self.balance_remaining = self.total_amount - self.amount_paid
        
        # Set maturity date if disbursement date is set and maturity date is not
        if self.disbursement_date and not self.maturity_date:
            from datetime import timedelta
            if self.repayment_frequency == 'daily' and self.term_days:
                self.maturity_date = (self.disbursement_date + timedelta(days=self.term_days)).date()
            elif self.repayment_frequency == 'weekly' and self.term_weeks:
                self.maturity_date = (self.disbursement_date + timedelta(weeks=self.term_weeks)).date()
            
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if loan has any overdue payments"""
        if self.status != 'active':
            return False
        
        from payments.models import PaymentSchedule
        from datetime import date
        
        return PaymentSchedule.objects.filter(
            loan=self,
            is_paid=False,
            due_date__lt=date.today()
        ).exists()
    
    @property
    def days_overdue(self):
        """Get number of days loan is overdue"""
        if not self.is_overdue:
            return 0
        
        from payments.models import PaymentSchedule
        from datetime import date
        
        oldest_overdue = PaymentSchedule.objects.filter(
            loan=self,
            is_paid=False,
            due_date__lt=date.today()
        ).order_by('due_date').first()
        
        if oldest_overdue:
            return (date.today() - oldest_overdue.due_date).days
        return 0
    
    @property
    def next_payment_due(self):
        """Get the next payment due date"""
        from payments.models import PaymentSchedule
        
        next_payment = PaymentSchedule.objects.filter(
            loan=self,
            is_paid=False
        ).order_by('due_date').first()
        
        return next_payment.due_date if next_payment else None
    
    @property
    def completion_percentage(self):
        """Calculate loan completion percentage"""
        if not self.total_amount or self.total_amount == 0:
            return 0
        
        return min(100, (self.amount_paid / self.total_amount) * 100)
    
    def can_be_disbursed(self):
        """Check if loan can be disbursed"""
        # Must be approved
        if self.status != 'approved':
            return False
        
        # Security deposit must be verified
        if not self.upfront_payment_verified:
            return False
        
        # Client must have verified documents (NRC front, NRC back, selfie)
        try:
            from documents.models import ClientVerification
            verification = ClientVerification.objects.get(client=self.borrower)
            if not verification.can_apply_for_loan():
                return False
        except:
            # If documents app not available or verification doesn't exist, allow
            pass
        
        # High-value loans (K6,000+) need admin approval
        if self.principal_amount >= 6000:
            try:
                approval_request = self.approval_request
                if approval_request.status != 'approved':
                    return False
            except:
                return False
        
        return True
    
    def has_paid_upfront(self):
        """Check if upfront payment has been made and verified"""
        return self.upfront_payment_verified and self.upfront_payment_paid >= self.upfront_payment_required
    
    def can_receive_payments(self):
        """Check if loan can receive payments"""
        return self.status == 'active'
    
    def can_be_approved_by_manager(self):
        """Check if loan can be approved by manager"""
        # Loan must be in approved status
        if self.status != 'approved':
            return False, 'Loan is not in approved status.'
        
        # Security deposit must be verified
        try:
            if not self.security_deposit.is_verified:
                return False, 'Security deposit must be verified before approval.'
        except:
            return False, 'Security deposit not found.'
        
        return True, 'Loan can be approved.'
    
    def can_be_disbursed_by_manager(self):
        """Check if loan can be disbursed by manager"""
        # Loan must be in approved status
        if self.status != 'approved':
            return False, 'Loan is not in approved status.'
        
        # Security deposit must be verified
        try:
            if not self.security_deposit.is_verified:
                return False, 'Security deposit must be verified before disbursement.'
        except:
            return False, 'Security deposit not found.'
        
        # High-value loans must have admin approval
        if self.principal_amount >= 6000:
            try:
                if self.approval_request.status != 'approved':
                    return False, 'This high-value loan requires admin approval before disbursement.'
            except:
                return False, 'This high-value loan requires admin approval before disbursement.'
        
        return True, 'Loan can be disbursed.'
    
    class Meta:
        ordering = ['-created_at']


def loan_document_upload_path(instance, filename):
    """Generate upload path for loan documents"""
    # Create path: loan_documents/loan_id/document_type/filename
    return f'loan_documents/{instance.loan.id}/{instance.document_type}/{filename}'


class LoanDocument(models.Model):
    """Documents uploaded for loan applications"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('id_copy', 'ID Copy'),
        ('proof_of_income', 'Proof of Income'),
        ('bank_statement', 'Bank Statement'),
        ('employment_letter', 'Employment Letter'),
        ('business_license', 'Business License'),
        ('collateral_documents', 'Collateral Documents'),
        ('other', 'Other'),
    ]
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='loan_documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    document_file = models.FileField(upload_to=loan_document_upload_path)
    original_filename = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.loan.application_number}"
    
    def save(self, *args, **kwargs):
        if self.document_file and not self.original_filename:
            self.original_filename = os.path.basename(self.document_file.name)
        super().save(*args, **kwargs)
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        if self.document_file:
            return round(self.document_file.size / (1024 * 1024), 2)
        return 0
    
    @property
    def file_extension(self):
        """Get file extension"""
        if self.document_file:
            return os.path.splitext(self.original_filename)[1].lower()
        return ''
    
    class Meta:
        ordering = ['-uploaded_at']


class SecurityDeposit(models.Model):
    """Track security deposits (10% upfront payment) separately from regular payments"""
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('check', 'Check'),
    ]
    
    loan = models.OneToOneField(
        Loan,
        on_delete=models.CASCADE,
        related_name='security_deposit',
        help_text='Loan associated with this security deposit'
    )
    
    # Amount details
    required_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Required deposit amount (10% of principal)'
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Amount actually paid'
    )
    
    # Payment details
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date when deposit was paid'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        help_text='Method used for payment'
    )
    
    # Verification
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_deposits',
        help_text='Admin/Manager who verified the deposit'
    )
    verification_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date when deposit was verified'
    )
    is_verified = models.BooleanField(
        default=False,
        help_text='Has this deposit been verified by an admin?'
    )
    
    # Additional information
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this deposit'
    )
    receipt_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='Receipt or transaction reference number'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Security Deposit'
        verbose_name_plural = 'Security Deposits'
    
    def __str__(self):
        status = 'Verified' if self.is_verified else 'Pending'
        return f"Deposit for {self.loan.application_number} - {status}"
    
    @property
    def is_fully_paid(self):
        """Check if the full required amount has been paid"""
        return self.paid_amount >= self.required_amount
    
    @property
    def outstanding_amount(self):
        """Calculate remaining amount to be paid"""
        return max(Decimal('0'), self.required_amount - self.paid_amount)
    
    def verify(self, verified_by_user):
        """Mark deposit as verified"""
        from django.utils import timezone
        self.is_verified = True
        self.verified_by = verified_by_user
        self.verification_date = timezone.now()
        self.save(update_fields=['is_verified', 'verified_by', 'verification_date', 'updated_at'])
    
    def is_pending(self):
        """Check if deposit is pending verification"""
        return not self.is_verified
    
    def can_be_approved(self):
        """Check if deposit can be approved"""
        # Deposit must be pending (not yet verified)
        if self.is_verified:
            return False, 'Deposit has already been verified.'
        
        # Deposit must have been paid
        if self.paid_amount <= 0:
            return False, 'No payment has been recorded for this deposit.'
        
        return True, 'Deposit can be approved.'



class SecurityTopUpRequest(models.Model):
    """Request to add more security deposit to a loan"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='security_topup_requests'
    )
    
    # Request details
    requested_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Amount to add to security deposit'
    )
    reason = models.TextField(
        help_text='Reason for security top-up request'
    )
    
    # Status and approval
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_topups'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_topups',
        limit_choices_to={'role__in': ['manager', 'admin']}
    )
    
    # Dates
    requested_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_date']
        verbose_name = 'Security Top-Up Request'
        verbose_name_plural = 'Security Top-Up Requests'
    
    def __str__(self):
        return f"Top-up for {self.loan.application_number} - {self.requested_amount}"


class SecurityReturnRequest(models.Model):
    """Request to return security deposit after loan completion"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='security_return_requests'
    )
    
    # Return details
    return_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Amount to be returned'
    )
    reason = models.TextField(
        help_text='Reason for security return request'
    )
    
    # Status and approval
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_returns'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_returns',
        limit_choices_to={'role__in': ['manager', 'admin']}
    )
    
    # Dates
    requested_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_date']
        verbose_name = 'Security Return Request'
        verbose_name_plural = 'Security Return Requests'
    
    def __str__(self):
        return f"Return for {self.loan.application_number} - {self.return_amount}"


class LoanApprovalRequest(models.Model):
    """Track approval requests for high-value loans (K6,000+)"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    loan = models.OneToOneField(
        Loan,
        on_delete=models.CASCADE,
        related_name='approval_request'
    )
    
    # Approval details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_approvals'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_loans',
        limit_choices_to={'role': 'admin'}
    )
    
    # Dates
    requested_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_date']
        verbose_name = 'Loan Approval Request'
        verbose_name_plural = 'Loan Approval Requests'
    
    def __str__(self):
        return f"Approval for {self.loan.application_number}"


class ApprovalLog(models.Model):
    """Log all approval actions for security deposits, top-ups, returns, loans, and disbursements"""
    
    APPROVAL_TYPES = [
        ('security_deposit', 'Security Deposit'),
        ('security_topup', 'Security Top-Up'),
        ('security_return', 'Security Return'),
        ('loan_approval', 'Loan Approval'),
        ('loan_disbursement', 'Loan Disbursement'),
    ]
    
    ACTION_CHOICES = [
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ]
    
    # Approval details
    approval_type = models.CharField(
        max_length=20,
        choices=APPROVAL_TYPES,
        help_text="Type of approval"
    )
    
    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='approval_logs'
    )
    
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approval_logs'
    )
    
    action = models.CharField(
        max_length=10,
        choices=ACTION_CHOICES,
        help_text="Approve or Reject"
    )
    
    comments = models.TextField(
        blank=True,
        help_text="Optional comments about the approval/rejection"
    )
    
    branch = models.CharField(
        max_length=100,
        help_text="Branch where approval was made"
    )
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Approval Log'
        verbose_name_plural = 'Approval Logs'
        indexes = [
            models.Index(fields=['loan', '-timestamp']),
            models.Index(fields=['manager', '-timestamp']),
            models.Index(fields=['branch', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_approval_type_display()} - {self.get_action_display()} by {self.manager.full_name} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class ManagerLoanApproval(models.Model):
    """Track manager approval of loans for disbursement"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    loan = models.OneToOneField(
        Loan,
        on_delete=models.CASCADE,
        related_name='manager_approval',
        help_text='Loan being approved by manager'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Approval status'
    )
    
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loan_approvals',
        help_text='Manager who approved the loan'
    )
    
    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date when loan was approved'
    )
    
    comments = models.TextField(
        blank=True,
        help_text='Optional comments about the approval'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Manager Loan Approval'
        verbose_name_plural = 'Manager Loan Approvals'
        indexes = [
            models.Index(fields=['loan', '-created_at']),
            models.Index(fields=['manager', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Manager Approval for {self.loan.application_number} - {self.get_status_display()}"
