#!/usr/bin/env python
"""Check payment distribution for loan LV-000088"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import Loan
from payments.models import Payment, PaymentSchedule

# Get the loan
loan = Loan.objects.get(application_number='LV-000088')

print('=' * 60)
print('LOAN INFORMATION')
print('=' * 60)
print(f'Loan Number: {loan.application_number}')
print(f'Principal: K{loan.principal_amount}')
print(f'Payment Amount: K{loan.payment_amount}')
print(f'Status: {loan.status}')
print()

print('=' * 60)
print('PAYMENT RECORDS')
print('=' * 60)
payments = Payment.objects.filter(loan=loan).order_by('created_at')
print(f'Total Payment Records: {payments.count()}')
print()
for p in payments:
    print(f'Payment ID: {p.id}')
    print(f'  Amount: K{p.amount}')
    print(f'  Payment Date: {p.payment_date}')
    print(f'  Status: {p.status}')
    print(f'  Created At: {p.created_at}')
    print(f'  Recorded By: {p.recorded_by}')
    if p.payment_schedule:
        print(f'  Linked to Schedule: #{p.payment_schedule.installment_number}')
    print()

print('=' * 60)
print('PAYMENT SCHEDULES (First 5)')
print('=' * 60)
schedules = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')[:5]
for s in schedules:
    print(f'Schedule #{s.installment_number}')
    print(f'  Due Date: {s.due_date}')
    print(f'  Total Amount: K{s.total_amount}')
    print(f'  Amount Paid: K{s.amount_paid}')
    print(f'  Is Paid: {s.is_paid}')
    print(f'  Paid Date: {s.paid_date}')
    print()

print('=' * 60)
print('ANALYSIS')
print('=' * 60)
total_paid = sum(p.amount for p in payments if p.status == 'completed')
schedules_marked_paid = PaymentSchedule.objects.filter(loan=loan, is_paid=True).count()
print(f'Total Amount Paid (from Payment records): K{total_paid}')
print(f'Number of Schedules Marked as Paid: {schedules_marked_paid}')
print(f'Expected Schedules Paid (based on amount): {int(total_paid / loan.payment_amount)}')
print()

if schedules_marked_paid > int(total_paid / loan.payment_amount):
    print('⚠️  WARNING: More schedules marked as paid than expected!')
    print('   This indicates a payment distribution bug.')
