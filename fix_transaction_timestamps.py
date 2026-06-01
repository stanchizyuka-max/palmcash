#!/usr/bin/env python
"""
Fix transaction timestamps that are set to 00:00:00.

The issue: Transactions with time 00:00:00 were created AFTER month closing,
but they represent transactions that happened BEFORE month closing.

This script will:
1. Find all transactions with time 00:00:00 from June 1, 2026
2. Change their timestamp to be BEFORE the month closing (e.g., 09:00:00)
3. Delete month closing transactions
4. Recalculate all balances in correct chronological order
5. Recreate month closing transactions with correct amounts
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.utils import timezone
from decimal import Decimal
from clients.models import Branch
from loans.models import DailyVault, WeeklyVault
from expenses.models import VaultTransaction
from datetime import datetime, time

def fix_timestamps():
    """Fix transactions with 00:00:00 timestamp."""
    print("\n" + "=" * 80)
    print("STEP 1: FIXING TRANSACTION TIMESTAMPS")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    # Find transactions with time 00:00:00 (excluding month closing)
    midnight_txs = VaultTransaction.objects.filter(
        transaction_date__gte=today_start,
        transaction_date__time=time(0, 0, 0)
    ).exclude(
        transaction_type='month_close'
    ).order_by('branch', 'vault_type', 'id')
    
    if not midnight_txs.exists():
        print("✅ No transactions with 00:00:00 timestamp found")
        return
    
    print(f"⚠️  Found {midnight_txs.count()} transaction(s) with 00:00:00 timestamp")
    print("These will be changed to 09:00:00 (before month closing)")
    
    # Change timestamp to 09:00:00 (before month closing which is around 10:00-16:00)
    new_time = timezone.make_aware(datetime.combine(today, time(9, 0, 0)))
    
    for tx in midnight_txs:
        print(f"\n   TX #{tx.id}: {tx.get_transaction_type_display()}")
        print(f"   Branch: {tx.branch}")
        print(f"   Amount: K{tx.amount:,.2f}")
        print(f"   Old Time: {tx.transaction_date.strftime('%H:%M:%S')}")
        
        tx.transaction_date = new_time
        tx.save(update_fields=['transaction_date'])
        
        print(f"   New Time: 09:00:00")
    
    print(f"\n✅ Updated {midnight_txs.count()} transaction(s)")

def delete_month_closings():
    """Delete all month closing transactions."""
    print("\n" + "=" * 80)
    print("STEP 2: DELETING MONTH CLOSING TRANSACTIONS")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    month_closings = VaultTransaction.objects.filter(
        transaction_type='month_close',
        transaction_date__gte=today_start
    )
    
    if not month_closings.exists():
        print("✅ No month closing transactions found")
        return
    
    print(f"⚠️  Found {month_closings.count()} month closing transaction(s) to delete")
    
    for tx in month_closings:
        print(f"   Deleting TX #{tx.id}: {tx.branch} - {tx.vault_type.upper()} - K{tx.amount:,.2f}")
        tx.delete()
    
    print(f"\n✅ Deleted {month_closings.count()} transaction(s)")

def recalculate_and_create_closings():
    """Recalculate balances and create new month closing transactions."""
    print("\n" + "=" * 80)
    print("STEP 3: RECALCULATING BALANCES AND CREATING MONTH CLOSINGS")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    closing_time = timezone.make_aware(datetime.combine(today, time(23, 59, 59)))
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    summary = []
    
    for branch in branches:
        print(f"\n📍 {branch.name}")
        
        # Process each vault type
        for vault_type in ['daily', 'weekly']:
            # Get all transactions for this vault from today (excluding month closing)
            transactions = VaultTransaction.objects.filter(
                branch__iexact=branch.name,
                vault_type=vault_type,
                transaction_date__gte=today_start
            ).exclude(
                transaction_type='month_close'
            ).order_by('transaction_date', 'id')
            
            if not transactions.exists():
                continue
            
            # Recalculate balance_after for each transaction
            running_balance = Decimal('0.00')
            
            for tx in transactions:
                if tx.direction == 'in':
                    running_balance += tx.amount
                else:
                    running_balance -= tx.amount
                
                if tx.balance_after != running_balance:
                    tx.balance_after = running_balance
                    tx.save(update_fields=['balance_after'])
            
            # The balance at end of day (before closing) is the running_balance
            balance_before_closing = running_balance
            
            # Create month closing transaction if balance > 0
            if balance_before_closing != Decimal('0.00'):
                closing_tx = VaultTransaction.objects.create(
                    transaction_type='month_close',
                    direction='out',
                    branch=branch.name,
                    vault_type=vault_type,
                    amount=balance_before_closing,
                    balance_after=Decimal('0.00'),
                    description=f'Month closing - {today.strftime("%B %Y")}',
                    reference_number=f'MC-{branch.name[:3].upper()}-{vault_type[:1].upper()}-{today.strftime("%Y%m%d")}',
                    recorded_by=None,
                    approved_by=None,
                    transaction_date=closing_time,
                )
                
                print(f"   {vault_type.capitalize()}: Created month closing K{balance_before_closing:,.2f}")
                
                # Final balance is 0 after closing
                final_balance = Decimal('0.00')
            else:
                print(f"   {vault_type.capitalize()}: No closing needed (balance is K0.00)")
                final_balance = Decimal('0.00')
            
            # Calculate inflows and outflows (excluding month closing)
            inflows = sum(tx.amount for tx in transactions.filter(direction='in'))
            outflows = sum(tx.amount for tx in transactions.filter(direction='out'))
            
            # Update vault model
            if vault_type == 'daily':
                vault, _ = DailyVault.objects.get_or_create(branch=branch)
            else:
                vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
            
            vault.balance = final_balance
            vault.total_inflows = inflows
            vault.total_outflows = outflows
            vault.save(update_fields=['balance', 'total_inflows', 'total_outflows'])
            
            print(f"      Balance: K{final_balance:,.2f} (In: K{inflows:,.2f}, Out: K{outflows:,.2f})")
        
        # Get final totals
        daily_vault = DailyVault.objects.filter(branch=branch).first()
        weekly_vault = WeeklyVault.objects.filter(branch=branch).first()
        
        daily_balance = daily_vault.balance if daily_vault else Decimal('0.00')
        weekly_balance = weekly_vault.balance if weekly_vault else Decimal('0.00')
        total_balance = daily_balance + weekly_balance
        
        summary.append({
            'branch': branch.name,
            'daily': daily_balance,
            'weekly': weekly_balance,
            'total': total_balance,
        })
    
    return summary

def main():
    print("=" * 80)
    print("FIXING TRANSACTION TIMESTAMPS AND MONTH CLOSINGS")
    print("=" * 80)
    print("\n⚠️  This will:")
    print("   1. Change transactions with 00:00:00 time to 09:00:00")
    print("   2. Delete existing month closing transactions")
    print("   3. Recalculate all balances in correct order")
    print("   4. Create new month closing transactions with correct amounts")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    # Step 1: Fix timestamps
    fix_timestamps()
    
    # Step 2: Delete month closings
    delete_month_closings()
    
    # Step 3: Recalculate and create new closings
    summary = recalculate_and_create_closings()
    
    # Print summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY - ALL BRANCHES")
    print("=" * 80)
    
    for s in summary:
        print(f"\n📍 {s['branch']}")
        print(f"   Daily:  K{s['daily']:>12,.2f}")
        print(f"   Weekly: K{s['weekly']:>12,.2f}")
        print(f"   Total:  K{s['total']:>12,.2f}")
    
    print("\n" + "=" * 80)
    print("✅ All timestamps have been fixed")
    print("✅ Month closings have been recreated with correct amounts")
    print("✅ All balances are now K0.00 (as expected after month closing)")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
