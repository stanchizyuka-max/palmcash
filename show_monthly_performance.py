#!/usr/bin/env python
"""
Show monthly performance for all branches - what June brought in vs opening balance
This is what your employer wants to see!
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
from loans.models import DailyVault, WeeklyVault
from django.utils import timezone
from django.db.models import Sum, Q

def show_monthly_performance():
    """Show what each month brings in vs opening balance"""
    
    print("=" * 80)
    print("     MONTHLY PERFORMANCE REPORT - JUNE 2026")
    print("     What Each Branch Made This Month")
    print("=" * 80)
    print()
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    # June 1st start of day (after month closing)
    june_start = timezone.make_aware(datetime(2026, 6, 1, 0, 0, 0))
    # Today end of day
    today_end = timezone.now()
    
    for branch in branches:
        print(f"\n{'━' * 80}")
        print(f"  {branch.name.upper()}")
        print(f"{'━' * 80}")
        
        # Get opening balance from month closing transaction
        month_closing = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_type='month_close',
            transaction_date__gte=june_start
        ).order_by('transaction_date').first()
        
        if month_closing:
            opening_balance = month_closing.amount
            opening_date = month_closing.transaction_date
            print(f"  Opening Balance (from May):         K{opening_balance:>12,.2f}")
            print(f"  Opening Date:                       {opening_date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            opening_balance = Decimal('0')
            print(f"  Opening Balance (from May):         K{opening_balance:>12,.2f}")
            print(f"  (No month closing found)")
        
        print(f"  {'-' * 76}")
        
        # Get June transactions (AFTER month closing)
        june_txs = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_date__gte=june_start,
            transaction_date__lte=today_end
        ).exclude(
            transaction_type='month_close'  # Exclude the opening balance itself
        ).order_by('transaction_date')
        
        # Calculate June activity
        june_inflows = june_txs.filter(direction='in').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        june_outflows = june_txs.filter(direction='out').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        june_net = june_inflows - june_outflows
        
        print(f"  JUNE ACTIVITY (Jun 1 - {today_end.strftime('%b %d')}):")
        print(f"    Collections (IN):                 K{june_inflows:>12,.2f}")
        print(f"    Disbursements/Expenses (OUT):     K{june_outflows:>12,.2f}")
        print(f"  {'-' * 76}")
        print(f"  June Net Change:                    K{june_net:>12,.2f}")
        print(f"  {'-' * 76}")
        
        # Current vault balances
        daily_vault = DailyVault.objects.filter(branch=branch).first()
        weekly_vault = WeeklyVault.objects.filter(branch=branch).first()
        
        daily_balance = daily_vault.balance if daily_vault else Decimal('0')
        weekly_balance = weekly_vault.balance if weekly_vault else Decimal('0')
        current_total = daily_balance + weekly_balance
        
        print(f"  CURRENT VAULT BALANCES:")
        print(f"    Daily Vault:                      K{daily_balance:>12,.2f}")
        print(f"    Weekly Vault:                     K{weekly_balance:>12,.2f}")
        print(f"  {'-' * 76}")
        print(f"  Total Balance:                      K{current_total:>12,.2f}")
        print(f"  {'━' * 76}")
        
        # Verification
        expected_balance = opening_balance + june_net
        difference = current_total - expected_balance
        
        print(f"  VERIFICATION:")
        print(f"    Opening (K{opening_balance:,.2f}) + June Net (K{june_net:,.2f}) = K{expected_balance:,.2f}")
        print(f"    Current Balance:                  K{current_total:>12,.2f}")
        
        if abs(difference) < Decimal('0.01'):  # Within 1 cent
            print(f"    Status:                           ✅ BALANCED")
        else:
            print(f"    Difference:                       K{difference:>12,.2f} ⚠️")
        
        # Show recent transactions
        print(f"\n  RECENT JUNE TRANSACTIONS (last 5):")
        recent_txs = june_txs[:5]
        if recent_txs:
            for tx in recent_txs:
                direction_symbol = "+" if tx.direction == 'in' else "-"
                print(f"    {tx.transaction_date.strftime('%b %d %H:%M')} | "
                      f"{tx.get_transaction_type_display():<20} | "
                      f"{tx.vault_type.upper():<6} | "
                      f"{direction_symbol}K{tx.amount:>9,.2f}")
        else:
            print(f"    (No June transactions yet)")
    
    print(f"\n{'=' * 80}")
    print()
    print("SUMMARY:")
    print("--------")
    print("• Opening Balance = Cash from May that was in vault on May 31")
    print("• June Activity = Only transactions from June 1 onwards")
    print("• Current Balance = Opening + June Activity")
    print()
    print("TO TRACK 'WHAT JUNE BRINGS IN':")
    print("✅ Use the Activity Report in the system (Dashboard → Activity Report)")
    print("✅ Set date range: Jun 1 - Jun 30")
    print("✅ This shows ONLY June's performance (no opening balance)")
    print()
    print("VAULT PAGES show total cash on hand (includes previous months).")
    print("ACTIVITY REPORT shows monthly performance (excludes opening balance).")
    print("=" * 80)

if __name__ == '__main__':
    show_monthly_performance()
