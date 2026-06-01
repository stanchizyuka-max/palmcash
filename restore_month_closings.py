#!/usr/bin/env python
"""
Restore month closing transactions that were deleted.

This will recreate the month closing transactions with the amounts they had
before they were deleted.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.utils import timezone
from decimal import Decimal
from clients.models import Branch
from expenses.models import VaultTransaction
from datetime import datetime, time

def restore_month_closings():
    """Restore month closing transactions."""
    print("=" * 80)
    print("RESTORING MONTH CLOSING TRANSACTIONS")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    
    # Month closing data from before deletion
    closings = [
        {
            'branch': 'Chazanga',
            'vault_type': 'daily',
            'amount': Decimal('0.00'),
            'time': time(16, 2, 10),
        },
        {
            'branch': 'KAMWALA SOUTH',
            'vault_type': 'daily',
            'amount': Decimal('7505.00'),
            'time': time(10, 49, 19),
        },
        {
            'branch': 'KAMWALA SOUTH',
            'vault_type': 'weekly',
            'amount': Decimal('16713.00'),  # Corrected amount
            'time': time(10, 49, 19),
        },
        {
            'branch': 'KUKU',
            'vault_type': 'daily',
            'amount': Decimal('7805.00'),
            'time': time(10, 38, 27),
        },
        {
            'branch': 'KUKU',
            'vault_type': 'weekly',
            'amount': Decimal('16233.00'),
            'time': time(10, 38, 27),
        },
        {
            'branch': 'MANDEVU BRANCH',
            'vault_type': 'weekly',
            'amount': Decimal('12345.00'),  # Corrected amount
            'time': time(10, 43, 39),
        },
    ]
    
    print("\n⚠️  This will recreate the following month closing transactions:")
    
    for closing in closings:
        print(f"\n   {closing['branch']} - {closing['vault_type'].upper()}")
        print(f"   Amount: K{closing['amount']:,.2f}")
        print(f"   Time: {closing['time'].strftime('%H:%M:%S')}")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    print("\n" + "=" * 80)
    print("CREATING MONTH CLOSING TRANSACTIONS")
    print("=" * 80)
    
    for closing in closings:
        # Check if it already exists
        existing = VaultTransaction.objects.filter(
            branch__iexact=closing['branch'],
            vault_type=closing['vault_type'],
            transaction_type='month_close',
            transaction_date__date=today
        ).first()
        
        if existing:
            print(f"\n⚠️  {closing['branch']} - {closing['vault_type'].upper()}: Already exists (TX #{existing.id})")
            continue
        
        # Create the transaction
        closing_time = timezone.make_aware(datetime.combine(today, closing['time']))
        
        tx = VaultTransaction.objects.create(
            transaction_type='month_close',
            direction='out',
            branch=closing['branch'],
            vault_type=closing['vault_type'],
            amount=closing['amount'],
            balance_after=Decimal('0.00'),
            description=f'Month closing - {today.strftime("%B %Y")}',
            reference_number=f'MC-{closing["branch"][:3].upper()}-{closing["vault_type"][:1].upper()}-{today.strftime("%Y%m%d")}',
            recorded_by=None,
            approved_by=None,
            transaction_date=closing_time,
        )
        
        print(f"\n✅ {closing['branch']} - {closing['vault_type'].upper()}")
        print(f"   Created TX #{tx.id}: K{closing['amount']:,.2f}")
    
    print("\n" + "=" * 80)
    print("✅ Month closing transactions have been restored")
    print("=" * 80)

if __name__ == '__main__':
    restore_month_closings()
