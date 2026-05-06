#!/usr/bin/env python
"""
Fix System Date Issue
=====================
This script checks if the system date is correct and provides instructions to fix it.
"""

import os
import sys
import django
from datetime import datetime, timezone as dt_timezone

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.utils import timezone
from expenses.models import VaultTransaction

def main():
    print("=" * 80)
    print("SYSTEM DATE CHECK")
    print("=" * 80)
    
    # Get current system time
    now = timezone.now()
    print(f"\nCurrent Django timezone-aware time: {now}")
    print(f"Current system time (UTC): {datetime.now(dt_timezone.utc)}")
    print(f"Current system time (local): {datetime.now()}")
    
    # Get transaction date range
    first_tx = VaultTransaction.objects.order_by('transaction_date').first()
    last_tx = VaultTransaction.objects.order_by('-transaction_date').first()
    
    if first_tx and last_tx:
        print(f"\nTransaction date range:")
        print(f"  Earliest: {first_tx.transaction_date}")
        print(f"  Latest: {last_tx.transaction_date}")
        
        # Check if transactions are in the future
        if last_tx.transaction_date > now:
            days_ahead = (last_tx.transaction_date - now).days
            print(f"\n⚠ WARNING: Latest transaction is {days_ahead} days in the FUTURE!")
            print(f"  This means either:")
            print(f"    1. Your system date is set incorrectly (too far in the past)")
            print(f"    2. Transaction dates were entered incorrectly (too far in the future)")
            
            print(f"\n" + "=" * 80)
            print("RECOMMENDED FIX")
            print("=" * 80)
            print(f"\nOption 1: Update system date to match transaction dates")
            print(f"  Run this command as root:")
            print(f"  sudo timedatectl set-time '{last_tx.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}'")
            print(f"\nOption 2: Enable automatic time synchronization")
            print(f"  sudo timedatectl set-ntp true")
            
        elif first_tx.transaction_date < now:
            print(f"\n✓ Transaction dates are in the past (normal)")
            print(f"  Date filtering should work correctly.")
    else:
        print(f"\nNo transactions found in database.")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
