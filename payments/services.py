from decimal import Decimal
from datetime import date


def distribute_payment(loan, amount, payment_date=None):
    """
    Distribute a payment amount across pending installments in order.
    Marks installments as fully paid or partial as applicable.
    Returns list of (schedule, amount_applied) tuples.
    """
    from .models import PaymentSchedule
    amount = Decimal(str(amount))
    pay_date = payment_date or date.today()
    applied = []

    pending = PaymentSchedule.objects.filter(
        loan=loan, is_paid=False
    ).order_by('installment_number')

    remaining = amount
    for schedule in pending:
        if remaining <= 0:
            break

        outstanding = schedule.total_amount - schedule.amount_paid
        if outstanding <= 0:
            continue

        apply = min(remaining, outstanding)
        schedule.amount_paid += apply
        remaining -= apply

        if schedule.amount_paid >= schedule.total_amount:
            schedule.is_paid = True
            schedule.paid_date = pay_date
        schedule.save(update_fields=['amount_paid', 'is_paid', 'paid_date'])
        applied.append((schedule, apply))

    return applied
