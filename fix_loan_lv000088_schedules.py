#!/usr/bin/env python
"""
Fix payment schedule marking for loan LV-000088
Only 1 payment was made but 2 schedules were incorrectly marked as paid
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import Loan
from payments.models import Payment, PaymentSchedule
from decimal import Decimal

# Get the loan
loan = Loan.objects.get(application_number='LV-000088')

print('=' * 60)
print('FIXING LOAN LV-000088 PAYMENT SCHEDULES')
print('=' * 60)
print(f'Loan: {loan.application_number}')
print(f'Borrower: {loan.borrower.get_full_name()}')
print(f'Payment Amount: K{loan.payment_amount}')
print()

# Get all completed payments
payments = Payment.objects.filter(loan=loan, status='completed').order_by('payment_date')
print(f'Completed Payments: {payments.count()}')
for p in payments:
    print(f'  - Payment #{p.id}: K{p.amount} on {p.payment_date.date()}')
print()

# Calculate total paid
total_paid = sum(p.amount for p in payments)
print(f'Total Amount Paid: K{total_paid}')
print()

# Reset all schedules
print('Resetting all payment schedules...')
schedules = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')
for schedule in schedules:
    schedule.is_paid = False
    schedule.paid_date = None
    schedule.amount_paid = Decimal('0')
    schedule.save()
print(f'Reset {schedules.count()} schedules')
print()

# Redistribute payments correctly
print('Redistributing payments across schedules...')
from payments.services import distribute_payment

for payment in payments:
    print(f'Distributing payment #{payment.id} (K{payment.amount})...')
    applied = distribute_payment(loan, payment.amount, payment.payment_date.date())
    for schedule, amount in applied:
        print(f'  - Applied K{amount} to Schedule #{schedule.installment_number}')
print()

# Show final state
print('=' * 60)
print('FINAL STATE')
print('=' * 60)
schedules = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')[:5]
for s in schedules:
    status = 'PAID' if s.is_paid else ('PARTIAL' if s.amount_paid > 0 else 'PENDING')
    print(f'Schedule #{s.installment_number}: {status}')
    print(f'  Due: {s.due_date}')
    print(f'  Amount: K{s.total_amount}')
    print(f'  Paid: K{s.amount_paid}')
    if s.is_paid:
        print(f'  Paid Date: {s.paid_date}')
    print()

print('✅ Fix completed!')
