from datetime import datetime, timedelta
from decimal import Decimal
from payments.models import PaymentSchedule

def generate_payment_schedule(loan):
    """Generate payment schedule for a loan"""
    if loan.status not in ['disbursed', 'active']:
        return
    
    # Clear existing schedule
    PaymentSchedule.objects.filter(loan=loan).delete()
    
    # Determine term and payment frequency
    if loan.repayment_frequency == 'daily':
        term = loan.term_days
        frequency_days = 1
    elif loan.repayment_frequency == 'weekly':
        term = loan.term_weeks
        frequency_days = 7
    else:
        # Fallback for legacy monthly terms
        term = loan.term_months
        frequency_days = 30
    
    # If no term is set, try to calculate it from total amount and payment amount
    if not term or term <= 0:
        if loan.payment_amount and loan.payment_amount > 0:
            # Calculate total amount (principal + interest)
            total_amount = loan.principal_amount * (1 + loan.interest_rate / 100)
            # Calculate number of payments needed
            term = int(total_amount / loan.payment_amount)
            # Round up to ensure we cover the full amount
            if total_amount % loan.payment_amount > 0:
                term += 1
        else:
            # Cannot generate schedule without term or payment amount
            return
    
    # If still no valid term, cannot generate schedule
    if not term or term <= 0:
        return
    
    # Use the payment_amount directly (already includes interest)
    payment_amount = loan.payment_amount
    
    # Generate schedule
    start_date = loan.disbursement_date.date()
    
    for i in range(1, term + 1):
        # Calculate due date based on frequency
        due_date = start_date + timedelta(days=frequency_days * i)
        
        # For daily/weekly loans, we don't break down principal vs interest
        # The payment_amount is the total payment
        principal_amount = payment_amount
        interest_amount = Decimal('0')
        total_amount = payment_amount
        
        # Create payment schedule entry
        PaymentSchedule.objects.create(
            loan=loan,
            installment_number=i,
            due_date=due_date,
            principal_amount=round(principal_amount, 2),
            interest_amount=round(interest_amount, 2),
            total_amount=round(total_amount, 2)
        )
        
        if total_amount <= 0:
            break

def calculate_loan_summary(loan):
    """Calculate loan summary statistics"""
    from payments.models import Payment
    
    total_payments = Payment.objects.filter(
        loan=loan, 
        status='completed'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    scheduled_payments = PaymentSchedule.objects.filter(loan=loan)
    total_scheduled = scheduled_payments.aggregate(total=models.Sum('total_amount'))['total'] or 0
    paid_installments = scheduled_payments.filter(is_paid=True).count()
    overdue_installments = scheduled_payments.filter(
        is_paid=False,
        due_date__lt=datetime.now().date()
    ).count()
    
    return {
        'total_payments': total_payments,
        'total_scheduled': total_scheduled,
        'balance_remaining': total_scheduled - total_payments,
        'paid_installments': paid_installments,
        'total_installments': scheduled_payments.count(),
        'overdue_installments': overdue_installments,
    }
