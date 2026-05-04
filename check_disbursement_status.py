#!/usr/bin/env python
"""
Check the status of loan disbursements and vault transactions.
This helps diagnose why active loans and total disbursed might show 0.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import Loan
from expenses.models import VaultTransaction
from django.db.models import Sum, Count

print("=" * 80)
print("LOAN DISBURSEMENT STATUS CHECK")
print("=" * 80)

# Check active loans
active_loans = Loan.objects.filter(status='active')
print(f"\n📊 ACTIVE LOANS: {active_loans.count()}")

if active_loans.exists():
    total_principal = active_loans.aggregate(total=Sum('principal_amount'))['total'] or 0
    print(f"   Total Principal: K{total_principal:,.2f}")
    
    for loan in active_loans[:10]:  # Show first 10
        print(f"   - {loan.application_number}: K{loan.principal_amount:,.2f} | {loan.borrower.get_full_name()}")
    
    if active_loans.count() > 10:
        print(f"   ... and {active_loans.count() - 10} more")
else:
    print("   No active loans found")

# Check all disbursed loans
all_disbursed = Loan.objects.filter(
    status__in=['active', 'disbursed', 'completed', 'defaulted'],
    disbursement_date__isnull=False
)
print(f"\n📊 ALL DISBURSED LOANS: {all_disbursed.count()}")

if all_disbursed.exists():
    total_disbursed = all_disbursed.aggregate(total=Sum('principal_amount'))['total'] or 0
    print(f"   Total Disbursed: K{total_disbursed:,.2f}")
    
    # Breakdown by status
    status_breakdown = all_disbursed.values('status').annotate(
        count=Count('id'),
        total=Sum('principal_amount')
    ).order_by('-count')
    
    print("\n   Breakdown by Status:")
    for item in status_breakdown:
        print(f"   - {item['status']}: {item['count']} loans, K{item['total']:,.2f}")

# Check vault disbursement transactions
disbursement_txs = VaultTransaction.objects.filter(
    transaction_type='loan_disbursement',
    direction='out'
)
print(f"\n📊 VAULT DISBURSEMENT TRANSACTIONS: {disbursement_txs.count()}")

if disbursement_txs.exists():
    total_vault_disbursed = disbursement_txs.aggregate(total=Sum('amount'))['total'] or 0
    print(f"   Total in Vault: K{total_vault_disbursed:,.2f}")
    
    # Breakdown by vault type
    vault_breakdown = disbursement_txs.values('vault_type').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('vault_type')
    
    print("\n   Breakdown by Vault:")
    for item in vault_breakdown:
        vault_name = item['vault_type'].title() if item['vault_type'] else 'Unknown'
        print(f"   - {vault_name}: {item['count']} transactions, K{item['total']:,.2f}")

# Compare loans vs vault transactions
print("\n" + "=" * 80)
print("COMPARISON")
print("=" * 80)

if all_disbursed.exists():
    total_loan_amount = all_disbursed.aggregate(total=Sum('principal_amount'))['total'] or 0
    total_vault_amount = disbursement_txs.aggregate(total=Sum('amount'))['total'] or 0
    
    print(f"\nTotal Loan Disbursements:  K{total_loan_amount:,.2f}")
    print(f"Total Vault Disbursements: K{total_vault_amount:,.2f}")
    print(f"Difference:                K{(total_loan_amount - total_vault_amount):,.2f}")
    
    if total_loan_amount > total_vault_amount:
        missing = total_loan_amount - total_vault_amount
        print(f"\n⚠️  WARNING: K{missing:,.2f} in disbursements are missing from vault!")
        print(f"   This means {all_disbursed.count() - disbursement_txs.count()} loans were disbursed but not recorded in vault.")
        print(f"\n   💡 SOLUTION: Run 'python fix_missing_disbursement_transactions.py' to fix this.")
    elif total_loan_amount == total_vault_amount:
        print(f"\n✅ PERFECT: All loan disbursements are properly recorded in vault!")
    else:
        print(f"\n⚠️  WARNING: Vault has more disbursements than loans!")

# Check for loans without vault transactions
loans_without_vault = []
for loan in all_disbursed:
    vault_tx = VaultTransaction.objects.filter(
        loan=loan,
        transaction_type='loan_disbursement'
    ).first()
    if not vault_tx:
        loans_without_vault.append(loan)

if loans_without_vault:
    print(f"\n📋 LOANS WITHOUT VAULT TRANSACTIONS: {len(loans_without_vault)}")
    print("\n   First 10:")
    for loan in loans_without_vault[:10]:
        print(f"   - {loan.application_number}: K{loan.principal_amount:,.2f} | {loan.status} | {loan.disbursement_date.date()}")
    
    if len(loans_without_vault) > 10:
        print(f"   ... and {len(loans_without_vault) - 10} more")
else:
    print(f"\n✅ All disbursed loans have vault transactions!")

print("\n" + "=" * 80)
