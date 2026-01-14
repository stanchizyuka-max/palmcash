from django.db import models
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta

class PaymentSchedule(models.Model):
    """Payment schedule for each loan"""
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, related_name='payment_schedule')
    installment_number = models.IntegerField()
    due_date = models.DateField()
    principal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Payment {self.installment_number} for {self.loan.application_number}"
    
    @property
    def is_overdue(self):
        from datetime import date
        return not self.is_paid and self.due_date < date.today()
    
    @property
    def days_overdue(self):
        if self.is_overdue:
            from datetime import date
            return (date.today() - self.due_date).days
        return 0
    
    class Meta:
        ordering = ['installment_number']
        unique_together = ['loan', 'installment_number']

class Payment(models.Model):
    """Individual payment records"""
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('mobile_money', 'Mobile Money'),
        ('card', 'Card Payment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, related_name='payments')
    payment_schedule = models.ForeignKey(PaymentSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment Details
    payment_number = models.CharField(max_length=20, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Additional Details
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment {self.payment_number} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.payment_number:
            # Generate unique payment number
            last_payment = Payment.objects.order_by('-id').first()
            if last_payment:
                last_number = int(last_payment.payment_number.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.payment_number = f"PAY-{new_number:06d}"
        
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-payment_date']


class PaymentCollection(models.Model):
    """Track daily/weekly collection activities"""
    
    COLLECTION_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.CASCADE,
        related_name='collections'
    )
    
    # Collection details
    collection_date = models.DateField(
        help_text='Date when collection is scheduled'
    )
    expected_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount expected to be collected'
    )
    collected_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Actual amount collected'
    )
    
    # Collection status
    status = models.CharField(
        max_length=20,
        choices=COLLECTION_STATUS_CHOICES,
        default='scheduled'
    )
    
    # Payment type
    is_partial = models.BooleanField(
        default=False,
        help_text='Is this a partial payment?'
    )
    is_default = models.BooleanField(
        default=False,
        help_text='Is this a default collection (client missed payment)?'
    )
    is_late = models.BooleanField(
        default=False,
        help_text='Is this payment late?'
    )
    
    # Collection officer
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collections'
    )
    
    # Dates
    actual_collection_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the payment was actually collected'
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Notes about this collection'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-collection_date']
        unique_together = ['loan', 'collection_date']
        verbose_name = 'Payment Collection'
        verbose_name_plural = 'Payment Collections'
    
    def __str__(self):
        return f"Collection for {self.loan.application_number} on {self.collection_date}"
    
    @property
    def shortfall_amount(self):
        """Calculate amount short of expected"""
        return max(0, self.expected_amount - self.collected_amount)
    
    def mark_as_collected(self, amount, collected_by_user, notes=''):
        """Record collection"""
        from django.utils import timezone
        self.collected_amount = amount
        self.collected_by = collected_by_user
        self.actual_collection_date = timezone.now()
        self.status = 'completed'
        self.is_partial = amount < self.expected_amount
        self.notes = notes
        self.save()


class DefaultProvision(models.Model):
    """Track default provisions for missed payments"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('waived', 'Waived'),
    ]
    
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.CASCADE,
        related_name='default_provisions'
    )
    
    # Default details
    missed_payment_date = models.DateField(
        help_text='Date when payment was missed'
    )
    expected_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount that was expected'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Resolution
    resolved_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date when default was resolved'
    )
    resolution_notes = models.TextField(
        blank=True,
        help_text='How the default was resolved'
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-missed_payment_date']
        verbose_name = 'Default Provision'
        verbose_name_plural = 'Default Provisions'
    
    def __str__(self):
        return f"Default for {self.loan.application_number} on {self.missed_payment_date}"


class PassbookEntry(models.Model):
    """Track passbook entries for loans"""
    
    ENTRY_TYPE_CHOICES = [
        ('disbursement', 'Loan Disbursement'),
        ('security_deposit', 'Security Deposit'),
        ('payment', 'Payment'),
        ('penalty', 'Penalty'),
        ('interest', 'Interest'),
        ('other', 'Other'),
    ]
    
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.CASCADE,
        related_name='passbook_entries'
    )
    
    # Entry details
    entry_type = models.CharField(
        max_length=20,
        choices=ENTRY_TYPE_CHOICES
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    description = models.TextField(
        help_text='Description of the entry'
    )
    
    # Dates
    entry_date = models.DateField(
        help_text='Date of the entry'
    )
    recorded_date = models.DateTimeField(
        auto_now_add=True,
        help_text='When this entry was recorded'
    )
    
    # Recorded by
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='passbook_entries'
    )
    
    # Reference
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Reference number (e.g., payment number, receipt)'
    )
    
    class Meta:
        ordering = ['-entry_date']
        verbose_name = 'Passbook Entry'
        verbose_name_plural = 'Passbook Entries'
    
    def __str__(self):
        return f"{self.get_entry_type_display()} - {self.loan.application_number} - {self.amount}"


class MultiSchedulePayment(models.Model):
    """Payment that covers multiple payment schedules"""
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('mobile_money', 'Mobile Money'),
        ('card', 'Card Payment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.CASCADE,
        related_name='multi_schedule_payments'
    )
    
    # Payment details
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Total amount paid for multiple schedules'
    )
    payment_date = models.DateTimeField(
        help_text='Date and time when payment was made'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        help_text='Method used for payment'
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Transaction reference number'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this payment'
    )
    
    # Processing details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Payment status'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_multi_payments',
        help_text='Staff member who processed this payment'
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this payment was processed'
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Multi Payment K{self.total_amount} for {self.loan.application_number}"
    
    @property
    def schedules_covered(self):
        """Get the number of schedules covered by this payment"""
        return self.schedule_assignments.count()
    
    @property
    def covered_schedule_numbers(self):
        """Get the schedule numbers covered by this payment"""
        assignments = self.schedule_assignments.select_related('payment_schedule')
        return [assignment.payment_schedule.installment_number for assignment in assignments]
    
    def apply_to_schedules(self, schedule_ids):
        """Apply this payment to multiple schedules"""
        schedules = PaymentSchedule.objects.filter(
            id__in=schedule_ids,
            loan=self.loan,
            is_paid=False  # Only apply to unpaid schedules
        )
        
        total_assigned = Decimal('0')
        assignments_created = []
        
        for schedule in schedules:
            # Create assignment
            assignment = MultiSchedulePaymentAssignment.objects.create(
                multi_payment=self,
                payment_schedule=schedule,
                amount_applied=schedule.total_amount
            )
            assignments_created.append(assignment)
            total_assigned += schedule.total_amount
        
        # Check if the payment amount covers the schedules
        if total_assigned > self.total_amount:
            raise ValueError(f"Payment amount K{self.total_amount} is insufficient to cover K{total_assigned} in selected schedules")
        
        return assignments_created
    
    def approve_payment(self, processed_by):
        """Approve the payment and mark schedules as paid"""
        if self.status != 'pending':
            raise ValueError("Only pending payments can be approved")
        
        self.status = 'approved'
        self.processed_by = processed_by
        self.processed_at = timezone.now()
        self.save()
        
        # Mark all assigned schedules as paid
        for assignment in self.schedule_assignments.all():
            schedule = assignment.payment_schedule
            schedule.is_paid = True
            schedule.paid_date = self.payment_date.date()
            schedule.save()
        
        # Update loan balance
        self._update_loan_balance()
        
        # Check if loan is completed
        self._check_loan_completion()
    
    def _update_loan_balance(self):
        """Update loan balance after payment approval"""
        loan = self.loan
        loan.balance_remaining -= self.total_amount
        if loan.balance_remaining <= 0:
            loan.balance_remaining = 0
            loan.status = 'completed'
        loan.save()
    
    def _check_loan_completion(self):
        """Check if all schedules are paid and mark loan as completed"""
        unpaid_schedules = PaymentSchedule.objects.filter(
            loan=self.loan,
            is_paid=False
        ).count()
        
        if unpaid_schedules == 0:
            self.loan.status = 'completed'
            self.loan.save()
    
    class Meta:
        ordering = ['-payment_date']


class MultiSchedulePaymentAssignment(models.Model):
    """Link between multi-schedule payment and individual schedules"""
    
    multi_payment = models.ForeignKey(
        MultiSchedulePayment,
        on_delete=models.CASCADE,
        related_name='schedule_assignments'
    )
    
    payment_schedule = models.ForeignKey(
        PaymentSchedule,
        on_delete=models.CASCADE,
        related_name='multi_payment_assignments'
    )
    
    amount_applied = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount applied to this schedule'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['multi_payment', 'payment_schedule']
        ordering = ['payment_schedule__installment_number']
