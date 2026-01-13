#!/usr/bin/env python
"""
Debug script to check loan officer document verification data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from accounts.models import User
from documents.models import ClientVerification, ClientDocument
from django.db.models import Q

# Get a loan officer
loan_officers = User.objects.filter(role='loan_officer')
print(f"Total loan officers: {loan_officers.count()}")

if loan_officers.exists():
    officer = loan_officers.first()
    print(f"\nLoan Officer: {officer.full_name} (ID: {officer.id})")
    
    # Get assigned clients
    branch_clients = User.objects.filter(
        Q(assigned_officer=officer) | Q(group_memberships__group__assigned_officer=officer),
        role='borrower'
    ).distinct()
    
    print(f"Assigned clients: {branch_clients.count()}")
    for client in branch_clients[:5]:
        print(f"  - {client.full_name} (ID: {client.id})")
    
    branch_client_ids = branch_clients.values_list('id', flat=True)
    
    # Check ClientVerification records
    print(f"\n=== CLIENT VERIFICATIONS ===")
    all_verifications = ClientVerification.objects.filter(client_id__in=branch_client_ids)
    print(f"Total verifications: {all_verifications.count()}")
    
    for status in ['pending', 'documents_submitted', 'documents_rejected', 'verified', 'rejected']:
        count = all_verifications.filter(status=status).count()
        print(f"  {status}: {count}")
    
    # Check ClientDocument records
    print(f"\n=== CLIENT DOCUMENTS ===")
    all_documents = ClientDocument.objects.filter(client_id__in=branch_client_ids)
    print(f"Total documents: {all_documents.count()}")
    
    for status in ['pending', 'approved', 'rejected']:
        count = all_documents.filter(status=status).count()
        print(f"  {status}: {count}")
    
    # Show pending documents
    pending_docs = ClientDocument.objects.filter(
        client_id__in=branch_client_ids,
        status='pending'
    ).select_related('client')
    
    print(f"\n=== PENDING DOCUMENTS ===")
    print(f"Count: {pending_docs.count()}")
    for doc in pending_docs[:10]:
        print(f"  - {doc.client.full_name}: {doc.get_document_type_display()} (Status: {doc.status})")
    
    # Show pending verifications
    pending_verifs = ClientVerification.objects.filter(
        client_id__in=branch_client_ids,
        status__in=['documents_submitted', 'documents_rejected']
    )
    
    print(f"\n=== PENDING VERIFICATIONS ===")
    print(f"Count: {pending_verifs.count()}")
    for verif in pending_verifs[:10]:
        print(f"  - {verif.client.full_name}: {verif.status}")
else:
    print("No loan officers found")

# Check all ClientDocuments with pending status
print(f"\n=== ALL PENDING DOCUMENTS IN SYSTEM ===")
all_pending = ClientDocument.objects.filter(status='pending')
print(f"Total: {all_pending.count()}")
for doc in all_pending[:10]:
    print(f"  - {doc.client.full_name}: {doc.get_document_type_display()}")
