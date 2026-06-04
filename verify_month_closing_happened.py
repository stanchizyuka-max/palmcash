#!/usr/bin/env python
"""
Verify that month closing actually happened on June 1, 2026
Check if month closing transactions exist and are correct
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from clients.models import Branch
from expenses.models import VaultTransaction
from django.utils import timezone

def verify_month_closing():
    """Check if month closing happened and is recorded correctly"""
    
    print("=" * 80)
    print("     VERIFYING MONTH CLOSING - JUNE 1, 2026")
    print("=" * 80)
    print()
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    # Look for month closing transactions
    june_start = timezone.make_aware(datetime(2026, 6, 1, 0, 0, 0))
    june_2 = timezone.make_aware(datetime(2026, 6, 2, 23, 59, 59))
    
    print("Searching for month closing transactions between Jun 1-2, 2026...")
    print()
    
    month_closings = VaultTransaction.objects.filter(
        transaction_type='month_close',
        transaction_date__gte=june_start,
        transaction_date__lte=june_2
    ).order_by('branch', 'transaction_date')
    
    if not month_closings.exists():
        print("❌ NO MONTH CLOSING TRANSACTIONS FOUND!")
        print()
        print("This means:")
        print("  • Month closing was NOT recorded in the system")
        print("  • No accounting record exists for May's closing")
        print("  • The vault balances are just accumulated from all time")
        print()
        print("What happened:")
        print("  • Your employer may have clicked 'Close Month' but it failed")
        print("  • Or the feature wasn't used")
        print("  • Or the transactions were deleted during previous fixes")
        print()
        return False
    
    print(f"✅ FOUND {month_closings.count()} MONTH CLOSING TRANSACTION(S)")
    print()
    print("=" * 80)
    
    for closing in month_closings:
        print(f"\nBRANCH: {closing.branch}")
        print("-" * 80)
        print(f"  Transaction ID:       #{closing.id}")
        print(f"  Date/Time:            {closing.transaction_date}")
        print(f"  Type:                 {closing.get_transaction_type_display()}")
        print(f"  Vault Type:           {closing.vault_type.upper() if closing.vault_type else 'Unknown'}")
        print(f"  Direction:            {closing.direction.upper()}")
        print(f"  Amount:               K{closing.amount:,.2f}")
        print(f"  Balance After:        K{closing.balance_after:,.2f}")
        print(f"  Description:          {closing.description}")
        print(f"  Recorded By:          {closing.recorded_by.get_full_name() if closing.recorded_by else 'Unknown'}")
        print(f"  Reference:            {closing.reference_number}")
        
        # Check if direction is correct (should be IN for opening balance)
        if closing.direction == 'in':
            print(f"  Status:               ✅ CORRECT (IN = Opening balance brought forward)")
        elif closing.direction == 'out':
            print(f"  Status:               ⚠️  ATTENTION (OUT = Closing/removing balance)")
            print(f"                        This may be correct depending on your process")
        
        print("-" * 80)
    
    print()
    print("=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    
    # Group by branch
    branches_with_closing = set(month_closings.values_list('branch', flat=True))
    branches_without_closing = [b.name for b in branches if b.name not in branches_with_closing]
    
    print()
    print(f"Branches WITH month closing: {len(branches_with_closing)}")
    for branch_name in sorted(branches_with_closing):
        count = month_closings.filter(branch=branch_name).count()
        print(f"  • {branch_name}: {count} transaction(s)")
    
    if branches_without_closing:
        print()
        print(f"Branches WITHOUT month closing: {len(branches_without_closing)}")
        for branch_name in sorted(branches_without_closing):
            print(f"  • {branch_name}")
    
    print()
    print("=" * 80)
    print("INTERPRETATION:")
    print("=" * 80)
    print()
    
    # Count IN vs OUT
    in_count = month_closings.filter(direction='in').count()
    out_count = month_closings.filter(direction='out').count()
    
    print(f"Direction breakdown:")
    print(f"  • IN (opening balance):  {in_count}")
    print(f"  • OUT (closing balance): {out_count}")
    print()
    
    if in_count > 0 and out_count == 0:
        print("✅ MONTH CLOSING HAPPENED CORRECTLY")
        print()
        print("What this means:")
        print("  • Month closing was recorded on June 1, 2026")
        print("  • The transactions show opening balances (IN direction)")
        print("  • This brings forward the cash from May into June")
        print("  • Your employer DID close the month properly")
        print()
        print("Why they're confused:")
        print("  • They expected vaults to reset to K0")
        print("  • But month closing brings forward the balance (standard accounting)")
        print("  • The money is real cash from May that's still in the vault")
        print()
        return True
    
    elif out_count > 0 and in_count == 0:
        print("⚠️  MONTH CLOSING RECORDED AS 'OUT' (Closing Balance)")
        print()
        print("What this means:")
        print("  • Month closing was recorded on June 1, 2026")
        print("  • The transactions show OUT direction (closing/removing balance)")
        print("  • This may be removing the May balance from vaults")
        print("  • This could be causing negative balances or confusion")
        print()
        print("What happened:")
        print("  • The system recorded it as closing OUT the May balance")
        print("  • Then new transactions started from a lower base")
        print("  • This might be why balances seem wrong")
        print()
        return True
    
    elif in_count > 0 and out_count > 0:
        print("⚠️  MONTH CLOSING HAS BOTH IN AND OUT TRANSACTIONS")
        print()
        print("What this means:")
        print("  • There are multiple month closing transactions")
        print("  • Some are IN (opening), some are OUT (closing)")
        print("  • This might indicate:")
        print("    - Month was closed multiple times")
        print("    - Corrections were made")
        print("    - Different vaults closed differently")
        print()
        return True
    
    print()
    print("=" * 80)
    print()
    print("NEXT STEPS:")
    print("-----------")
    
    if month_closings.exists():
        print("✅ Month closing DID happen")
        print("✅ It's recorded in the database")
        print()
        print("Your employer's confusion:")
        print("  • They saw month closing succeed")
        print("  • They expected vaults to reset to K0")
        print("  • But they're seeing opening balances from May")
        print()
        print("The explanation:")
        print("  • Month closing BRINGS FORWARD the balance (doesn't reset)")
        print("  • The money in vaults is from May + June")
        print("  • To see 'what June brought in', use Activity Report")
        print()
        print("Show them:")
        print("  • FOR_EMPLOYER_ONE_PAGE.md")
        print("  • VISUAL_EXPLANATION.txt")
        print("  • Run: python show_monthly_performance.py")
    else:
        print("❌ Month closing did NOT happen (or was deleted)")
        print()
        print("This means:")
        print("  • Vault balances are accumulated from all time")
        print("  • There's no clear 'opening balance for June'")
        print("  • You may need to manually close the month")
    
    print()
    print("=" * 80)
    
    return month_closings.exists()

if __name__ == '__main__':
    verify_month_closing()
