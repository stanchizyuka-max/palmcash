#!/usr/bin/env python
"""
Investigate reversal transactions that are causing negative balances.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.utils import timezone
from clients.models import Branch
from expenses.models import VaultTransaction
from datetime import datetime

def main():
    print("=" * 80)
    print("INVESTIGATING REVERSAL TRANSACTIONS")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    for branch in branches:
        print(f"\n{'=' * 80}")
        print(f"📍 BRANCH: {branch.name}")
        print(f"{'=' * 80}")
        
        # Find transactions with "Reversed" in description or recorded_by
        reversed_txs = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_date__gte=today_start
        ).filter(
            recorded_by__username__icontains='reversed'
        ) | VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_date__gte=today_start,
            description__icontains='REVERSAL'
        )
        
        if reversed_txs.exists():
            print(f"\n⚠️  Found {reversed_txs.count()} reversal transaction(s):")
            for tx in reversed_txs.order_by('-transaction_date'):
                print(f"\n   TX #{tx.id}:")
                print(f"   Type: {tx.transaction_type}")
                print(f"   Direction: {tx.direction.upper()}")
                print(f"   Amount: K{tx.amount:,.2f}")
                print(f"   Balance After: K{tx.balance_after:,.2f}")
                print(f"   Date: {tx.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Recorded By: {tx.recorded_by.get_full_name() if tx.recorded_by else 'N/A'}")
                print(f"   Description: {tx.description}")
        else:
            print("\n✅ No reversal transactions found")
        
        # Also check for payment collections with direction OUT (unusual)
        unusual_payments = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_date__gte=today_start,
            transaction_type='payment_collection',
            direction='out'
        )
        
        if unusual_payments.exists():
            print(f"\n⚠️  Found {unusual_payments.count()} payment collection(s) with direction OUT:")
            for tx in unusual_payments.order_by('-transaction_date'):
                print(f"\n   TX #{tx.id}:")
                print(f"   Amount: K{tx.amount:,.2f}")
                print(f"   Balance After: K{tx.balance_after:,.2f}")
                print(f"   Loan: {tx.loan.application_number if tx.loan else 'N/A'}")
                print(f"   Recorded By: {tx.recorded_by.get_full_name() if tx.recorded_by else 'N/A'}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n⚠️  These reversal transactions are causing negative balances")
    print("⚠️  They need to be investigated and possibly deleted")
    print("\nPossible causes:")
    print("1. Someone manually reversed payment collections")
    print("2. A bug in the payment reversal code")
    print("3. Duplicate transactions being created")
    print("=" * 80)

if __name__ == '__main__':
    main()
