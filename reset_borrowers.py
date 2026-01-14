#!/usr/bin/env python
"""
Script to delete all borrowers and their related data
Run with: python manage.py shell < reset_borrowers.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db import transaction
from accounts.models import User
from loans.models import Loan, LoanApprovalRequest, SecurityDeposit, PaymentSchedule
from payments.models import PaymentCollection, PassbookEntry, MultiSchedulePayment
from documents.models import ClientDocument, ClientVerification
from clients.models import BorrowerGroup

print("Starting borrower and loan data deletion...")

with transaction.atomic():
    # Get all borrowers
    borrowers = User.objects.filter(role='borrower')
    borrower_count = borrowers.count()
    
    print(f"Found {borrower_count} borrowers to delete")
    
    # Delete related data first
    # Delete payment collections
    payment_collections = PaymentCollection.objects.filter(
        loan__borrower__in=borrowers
    )
    pc_count = payment_collections.count()
    payment_collections.delete()
    print(f"Deleted {pc_count} payment collections")
    
    # Delete passbook entries
    passbook_entries = PassbookEntry.objects.filter(
        loan__borrower__in=borrowers
    )
    pb_count = passbook_entries.count()
    passbook_entries.delete()
    print(f"Deleted {pb_count} passbook entries")
    
    # Delete multi-schedule payments
    multi_payments = MultiSchedulePayment.objects.filter(
        loan__borrower__in=borrowers
    )
    mp_count = multi_payments.count()
    multi_payments.delete()
    print(f"Deleted {mp_count} multi-schedule payments")
    
    # Delete payment schedules
    payment_schedules = PaymentSchedule.objects.filter(
        loan__borrower__in=borrowers
    )
    ps_count = payment_schedules.count()
    payment_schedules.delete()
    print(f"Deleted {ps_count} payment schedules")
    
    # Delete security deposits
    security_deposits = SecurityDeposit.objects.filter(
        loan__borrower__in=borrowers
    )
    sd_count = security_deposits.count()
    security_deposits.delete()
    print(f"Deleted {sd_count} security deposits")
    
    # Delete loan approval requests
    loan_approvals = LoanApprovalRequest.objects.filter(
        loan__borrower__in=borrowers
    )
    la_count = loan_approvals.count()
    loan_approvals.delete()
    print(f"Deleted {la_count} loan approval requests")
    
    # Delete client documents
    client_docs = ClientDocument.objects.filter(
        client__in=borrowers
    )
    cd_count = client_docs.count()
    client_docs.delete()
    print(f"Deleted {cd_count} client documents")
    
    # Delete client verifications
    client_verifs = ClientVerification.objects.filter(
        client__in=borrowers
    )
    cv_count = client_verifs.count()
    client_verifs.delete()
    print(f"Deleted {cv_count} client verifications")
    
    # Delete loans
    loans = Loan.objects.filter(borrower__in=borrowers)
    loan_count = loans.count()
    loans.delete()
    print(f"Deleted {loan_count} loans")
    
    # Remove borrowers from groups
    for borrower in borrowers:
        borrower.group_memberships.all().delete()
    print(f"Removed borrowers from groups")
    
    # Delete borrower users
    borrowers.delete()
    print(f"Deleted {borrower_count} borrower users")

print("\n✓ All borrower data has been successfully deleted!")
print("You can now start fresh with new borrowers and loans.")
