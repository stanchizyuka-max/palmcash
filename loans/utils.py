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
        term = loan.term_months
        frequency_days = 30
    
    if not term or term <= 0:
        if loan.payment_amount and loan.payment_amount > 0:
            total_amount = loan.principal_amount * (1 + loan.interest_rate / 100)
            term = int(total_amount / loan.payment_amount)
            if total_amount % loan.payment_amount > 0:
                term += 1
        else:
            return
    
    if not term or term <= 0:
        return
    
    payment_amount = loan.payment_amount
    start_date = loan.disbursement_date.date()
    
    installment = 1
    current_date = start_date

    for _ in range(term):
        current_date += timedelta(days=frequency_days)

        # For daily loans: skip Sundays (weekday 6)
        if loan.repayment_frequency == 'daily':
            while current_date.weekday() == 6:  # 6 = Sunday
                current_date += timedelta(days=1)

        PaymentSchedule.objects.create(
            loan=loan,
            installment_number=installment,
            due_date=current_date,
            principal_amount=round(payment_amount, 2),
            interest_amount=Decimal('0'),
            total_amount=round(payment_amount, 2),
        )
        installment += 1

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
