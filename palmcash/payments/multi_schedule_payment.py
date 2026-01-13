"""
Enhanced payment system to support multiple schedule payments
"""
from django.db import models
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta

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
        from .models import PaymentSchedule
        
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
        self.processed_at = datetime.now()
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
        from .models import PaymentSchedule
        
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
        'payments.PaymentSchedule',
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
