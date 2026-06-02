#!/usr/bin/env python
"""
EMERGENCY: Rebuild vault transactions from payment and loan records.

This script will recreate vault transactions for June 1, 2026 by looking at:
1. Payment records from the payments table
2. Loan disbursement records
3. Existing month closing transactions (which we have)

WARNING: This will only work if payment and loan tables still have their data!
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.utils import timezone
from decimal import Decimal
from clients.models import Branch
from loans.models import Loan, DailyVault, WeeklyVault
from expenses.models import VaultTransaction
from payments.models import Payment
from datetime import datetime, date
import uuid

def check_payment_data():
    """Check if payment data still exists."""
    print("=" * 80)
    print("CHECKING FOR PAYMENT DATA")
    print("=" * 80)
    
    today = date(2026, 6, 1)
    
    payments_today = Payment.objects.filter(payment_date=today)
    
    print(f"\nPayments found for June 1, 2026: {payments_today.count()}")
    
    if payments_today.count() > 0:
        print("\n✅ Payment data exists! We can rebuild vault transactions.")
        
        # Show summary by branch
        from django.db.models import Sum, Count
        by_branch = payments_today.values('loan__borrower__officer__branch__name').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        print("\nPayments by branch:")
        for item in by_branch:
            branch_name = item['loan__borrower__officer__branch__name'] or 'Unknown'
            print(f"   {branch_name}: {item['count']} payment(s), Total: K{item['total']:,.2f}")
        
        return True
    else:
        print("\n❌ No payment data found for June 1, 2026")
        print("   Cannot rebuild vault transactions without payment data.")
        return False

def rebuild_vault_transactions():
    """Rebuild vault transactions from payment records."""
    print("\n" + "=" * 80)
    print("REBUILDING VAULT TRANSACTIONS")
    print("=" * 80)
    
    today = date(2026, 6, 1)
    payments_today = Payment.objects.filter(payment_date=today).order_by('payment_date', 'id')
    
    if not payments_today.exists():
        print("❌ No payments to rebuild from")
        return
    
    created_count = 0
    
    for payment in payments_today:
        # Get loan details
        loan = payment.loan
        if not loan or not loan.borrower or not loan.borrower.officer or not loan.borrower.officer.branch:
            print(f"⚠️  Skipping payment #{payment.id} - missing loan/borrower/branch info")
            continue
        
        branch = loan.borrower.officer.branch
        vault_type = 'daily' if loan.loan_type == 'daily' else 'weekly'
        
        # Check if transaction already exists
        existing = VaultTransaction.objects.filter(
            payment=payment,
            branch__iexact=branch.name,
            vault_type=vault_type,
            transaction_type='payment_collection'
        ).first()
        
        if existing:
            continue  # Skip if already exists
        
        # Create vault transaction
        tx_time = timezone.make_aware(datetime.combine(today, datetime.strptime(payment.created_at.strftime('%H:%M:%S'), '%H:%M:%S').time()))
        
        try:
            tx = VaultTransaction.objects.create(
                transaction_type='payment_collection',
                direction='in',
                branch=branch.name,
                vault_type=vault_type,
                amount=payment.amount,
                balance_after=Decimal('0.00'),  # Will recalculate later
                description=f'Payment collection from {loan.borrower.get_full_name()} - {loan.application_number}',
                reference_number=f'PMT-{payment.id}-{uuid.uuid4().hex[:4].upper()}',
                loan=loan,
                payment=payment,
                recorded_by=payment.recorded_by,
                approved_by=payment.recorded_by,
                transaction_date=tx_time,
            )
            created_count += 1
            print(f"✅ Created: {branch.name} - {vault_type.upper()} - K{payment.amount:,.2f} - {loan.application_number}")
        except Exception as e:
            print(f"❌ Error creating transaction for payment #{payment.id}: {e}")
    
    print(f"\n✅ Created {created_count} vault transaction(s) from payment records")

def recalculate_all_balances():
    """Recalculate balance_after for all transactions in chronological order."""
    print("\n" + "=" * 80)
    print("RECALCULATING BALANCES")
    print("=" * 80)
    
    today = date(2026, 6, 1)
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    for branch in branches:
        print(f"\n📍 {branch.name}")
        
        for vault_type in ['daily', 'weekly']:
            # Get ALL transactions for this vault from today, in chronological order
            transactions = VaultTransaction.objects.filter(
                branch__iexact=branch.name,
                vault_type=vault_type,
                transaction_date__gte=today_start
            ).order_by('transaction_date', 'id')
            
            if not transactions.exists():
                print(f"   {vault_type.capitalize()}: No transactions")
                continue
            
            # Recalculate balance_after
            running_balance = Decimal('0.00')
            
            for tx in transactions:
                if tx.direction == 'in':
                    running_balance += tx.amount
                else:
                    running_balance -= tx.amount
                
                tx.balance_after = running_balance
                tx.save(update_fields=['balance_after'])
            
            # Calculate inflows and outflows
            inflows = sum(tx.amount for tx in transactions.filter(direction='in'))
            outflows = sum(tx.amount for tx in transactions.filter(direction='out'))
            
            # Update vault model
            if vault_type == 'daily':
                vault, _ = DailyVault.objects.get_or_create(branch=branch)
            else:
                vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
            
            vault.balance = running_balance
            vault.total_inflows = inflows
            vault.total_outflows = outflows
            vault.save(update_fields=['balance', 'total_inflows', 'total_outflows'])
            
            print(f"   {vault_type.capitalize()}: K{running_balance:,.2f} ({transactions.count()} tx, In: K{inflows:,.2f}, Out: K{outflows:,.2f})")

def main():
    print("=" * 80)
    print("EMERGENCY: REBUILD VAULT TRANSACTIONS FROM PAYMENTS")
    print("=" * 80)
    print("\n⚠️  This script will attempt to rebuild vault transactions by looking at")
    print("   payment records from June 1, 2026.")
    print("\n⚠️  This assumes that payment data still exists in the database!")
    
    # Step 1: Check if we have payment data
    if not check_payment_data():
        print("\n" + "=" * 80)
        print("CANNOT PROCEED - NO PAYMENT DATA FOUND")
        print("=" * 80)
        print("\nYou will need to restore from a database backup.")
        return
    
    response = input("\nDo you want to rebuild vault transactions? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    # Step 2: Rebuild vault transactions
    rebuild_vault_transactions()
    
    # Step 3: Recalculate all balances
    recalculate_all_balances()
    
    print("\n" + "=" * 80)
    print("REBUILD COMPLETE")
    print("=" * 80)
    print("\n✅ Vault transactions have been rebuilt from payment records")
    print("✅ Balances have been recalculated")
    print("\n⚠️  IMPORTANT:")
    print("   - Only PAYMENT COLLECTION transactions were rebuilt")
    print("   - Other transactions (expenses, bank deposits, etc.) are NOT included")
    print("   - Month closing transactions remain as they were")
    print("\n⚠️  Hard refresh your browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
