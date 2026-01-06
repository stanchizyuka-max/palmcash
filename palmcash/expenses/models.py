from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class ExpenseCode(models.Model):
    """Expense codes for categorization"""
    
    code = models.CharField(max_length=20, unique=True, help_text='Unique expense code (e.g., EXP-001)')
    name = models.CharField(max_length=100, help_text='Expense category name')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Expense Code'
        verbose_name_plural = 'Expense Codes'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ExpenseCategory(models.Model):
    """Categories for expenses"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Expense Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Expense(models.Model):
    """Track company expenses and vault transactions"""
    
    EXPENSE_TYPE_CHOICES = [
        ('operational', 'Operational Expense'),
        ('vault', 'Vault Transaction'),
        ('salary', 'Salary Payment'),
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    # Categorization
    expense_code = models.ForeignKey(
        ExpenseCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        help_text='Expense code for categorization'
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='expenses'
    )
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='operational')
    
    # Expense details
    title = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Branch and location
    branch = models.CharField(max_length=100, help_text='Branch where expense occurred')
    
    # Tracking
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_expenses'
    )
    
    # Approval workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_expenses',
        limit_choices_to={'role__in': ['manager', 'admin']}
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_comments = models.TextField(
        blank=True,
        help_text='Comments from approver'
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text='Reason for rejection if rejected'
    )
    
    # Dates
    expense_date = models.DateField(help_text='Date when expense occurred')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Attachments
    receipt = models.FileField(upload_to='expenses/receipts/', null=True, blank=True)
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
    
    def __str__(self):
        return f"{self.title} - K{self.amount} ({self.expense_date})"
    
    def approve(self, approved_by_user, comments=''):
        """Approve an expense"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approval_date = timezone.now()
        self.approval_comments = comments
        self.save(update_fields=['status', 'approved_by', 'approval_date', 'approval_comments', 'updated_at'])
        
        # Create approval log
        ExpenseApprovalLog.objects.create(
            expense=self,
            action='approved',
            approved_by=approved_by_user,
            comments=comments
        )
    
    def reject(self, rejected_by_user, reason=''):
        """Reject an expense"""
        self.status = 'rejected'
        self.approved_by = rejected_by_user
        self.approval_date = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=['status', 'approved_by', 'approval_date', 'rejection_reason', 'updated_at'])
        
        # Create approval log
        ExpenseApprovalLog.objects.create(
            expense=self,
            action='rejected',
            approved_by=rejected_by_user,
            comments=reason
        )


class VaultTransaction(models.Model):
    """Track vault cash movements"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Cash Deposit'),
        ('withdrawal', 'Cash Withdrawal'),
        ('transfer', 'Branch Transfer'),
        ('loan_disbursement', 'Loan Disbursement'),
        ('payment_collection', 'Payment Collection'),
    ]
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    branch = models.CharField(max_length=100)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Details
    description = models.TextField()
    reference_number = models.CharField(max_length=50, unique=True)
    
    # Related records
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vault_transactions'
    )
    payment = models.ForeignKey(
        'payments.Payment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vault_transactions'
    )
    
    # Tracking
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='vault_transactions'
    )
    
    transaction_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - K{self.amount} ({self.branch})"


class ExpenseApprovalLog(models.Model):
    """Log all expense approvals and rejections"""
    
    ACTION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('pending', 'Pending'),
    ]
    
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name='approval_logs'
    )
    
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='expense_approvals'
    )
    comments = models.TextField(
        blank=True,
        help_text='Approval or rejection comments'
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Expense Approval Log'
        verbose_name_plural = 'Expense Approval Logs'
    
    def __str__(self):
        return f"{self.expense} - {self.get_action_display()} by {self.approved_by} on {self.timestamp.date()}"


class FundsTransfer(models.Model):
    """Track funds transfers between branches"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    # Transfer details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Amount to transfer'
    )
    source_branch = models.CharField(
        max_length=100,
        help_text='Branch sending the funds'
    )
    destination_branch = models.CharField(
        max_length=100,
        help_text='Branch receiving the funds'
    )
    
    # Reference
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Transfer reference number'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of the transfer'
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
        related_name='requested_transfers'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_transfers',
        limit_choices_to={'role__in': ['manager', 'admin']}
    )
    
    # Dates
    requested_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    approval_comments = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_date']
        verbose_name = 'Funds Transfer'
        verbose_name_plural = 'Funds Transfers'
    
    def __str__(self):
        return f"Transfer K{self.amount} from {self.source_branch} to {self.destination_branch}"
    
    def approve(self, approved_by_user, comments=''):
        """Approve a transfer"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approval_date = timezone.now()
        self.approval_comments = comments
        self.save(update_fields=['status', 'approved_by', 'approval_date', 'approval_comments'])
    
    def reject(self, rejected_by_user, reason=''):
        """Reject a transfer"""
        self.status = 'rejected'
        self.approved_by = rejected_by_user
        self.approval_date = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=['status', 'approved_by', 'approval_date', 'rejection_reason'])
    
    def complete(self):
        """Mark transfer as completed"""
        self.status = 'completed'
        self.completion_date = timezone.now()
        self.save(update_fields=['status', 'completion_date'])


class BankDeposit(models.Model):
    """Track deposits into bank accounts"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    # Deposit details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Amount deposited'
    )
    source_branch = models.CharField(
        max_length=100,
        help_text='Branch depositing the funds'
    )
    bank_name = models.CharField(
        max_length=100,
        help_text='Name of the bank'
    )
    account_number = models.CharField(
        max_length=50,
        help_text='Bank account number'
    )
    
    # Reference
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Deposit reference number'
    )
    deposit_slip_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='Bank deposit slip number'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of the deposit'
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
        related_name='requested_deposits'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_deposits',
        limit_choices_to={'role__in': ['manager', 'admin']}
    )
    
    # Dates
    requested_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    deposit_date = models.DateField(null=True, blank=True, help_text='Date of actual deposit')
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    approval_comments = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_date']
        verbose_name = 'Bank Deposit'
        verbose_name_plural = 'Bank Deposits'
    
    def __str__(self):
        return f"Deposit K{self.amount} to {self.bank_name} from {self.source_branch}"
    
    def approve(self, approved_by_user, comments=''):
        """Approve a deposit"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approval_date = timezone.now()
        self.approval_comments = comments
        self.save(update_fields=['status', 'approved_by', 'approval_date', 'approval_comments'])
    
    def reject(self, rejected_by_user, reason=''):
        """Reject a deposit"""
        self.status = 'rejected'
        self.approved_by = rejected_by_user
        self.approval_date = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=['status', 'approved_by', 'approval_date', 'rejection_reason'])
    
    def complete(self):
        """Mark deposit as completed"""
        self.status = 'completed'
        self.completion_date = timezone.now()
        self.save(update_fields=['status', 'completion_date'])
