#!/usr/bin/env python
"""
Investigate vault discrepancies and daily vault operations
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
from django.db.models import Sum, Q, Count

def investigate():
    """Investigate vault discrepancies and daily vault usage"""
    
    print("=" * 80)
    print("     VAULT INVESTIGATION - Discrepancies and Daily Vault Usage")
    print("=" * 80)
    print()
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    june_start = timezone.make_aware(datetime(2026, 6, 1, 0, 0, 0))
    today = timezone.now()
    
    for branch in branches:
        print(f"\n{'═' * 80}")
        print(f"  {branch.name.upper()}")
        print(f"{'═' * 80}")
        
        # Get vault models
        daily_vault = DailyVault.objects.filter(branch=branch).first()
        weekly_vault = WeeklyVault.objects.filter(branch=branch).first()
        
        print(f"\n📊 VAULT MODEL BALANCES:")
        print(f"  Daily Vault:  K{daily_vault.balance if daily_vault else 0:,.2f}")
        print(f"  Weekly Vault: K{weekly_vault.balance if weekly_vault else 0:,.2f}")
        print(f"  Total:        K{(daily_vault.balance if daily_vault else 0) + (weekly_vault.balance if weekly_vault else 0):,.2f}")
        
        # Count transactions by vault type
        print(f"\n📝 TRANSACTION COUNT BY VAULT TYPE (June 1-4):")
        
        daily_count = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            vault_type='daily',
            transaction_date__gte=june_start,
            transaction_date__lte=today
        ).count()
        
        weekly_count = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            vault_type='weekly',
            transaction_date__gte=june_start,
            transaction_date__lte=today
        ).count()
        
        null_count = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            vault_type__isnull=True,
            transaction_date__gte=june_start,
            transaction_date__lte=today
        ).count()
        
        print(f"  Daily Vault Transactions:   {daily_count}")
        print(f"  Weekly Vault Transactions:  {weekly_count}")
        print(f"  No Vault Type (NULL):       {null_count}")
        
        if daily_count == 0:
            print(f"  ⚠️  NO DAILY VAULT TRANSACTIONS - Not using daily vault!")
        
        # Show recent transactions by vault type
        print(f"\n📋 RECENT DAILY VAULT TRANSACTIONS:")
        daily_txs = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            vault_type='daily',
            transaction_date__gte=june_start
        ).order_by('-transaction_date')[:5]
        
        if daily_txs.exists():
            for tx in daily_txs:
                direction_symbol = "+" if tx.direction == 'in' else "-"
                print(f"    {tx.transaction_date.strftime('%b %d %H:%M')} | "
                      f"{tx.get_transaction_type_display():<25} | "
                      f"{direction_symbol}K{tx.amount:>9,.2f} | "
                      f"Balance: K{tx.balance_after:,.2f}")
        else:
            print(f"    ❌ No daily vault transactions found")
        
        # Check if there are transactions without vault_type
        print(f"\n📋 TRANSACTIONS WITHOUT VAULT TYPE:")
        null_txs = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            vault_type__isnull=True,
            transaction_date__gte=june_start
        ).order_by('-transaction_date')[:5]
        
        if null_txs.exists():
            print(f"  ⚠️  Found {null_count} transactions without vault_type!")
            for tx in null_txs:
                direction_symbol = "+" if tx.direction == 'in' else "-"
                print(f"    TX #{tx.id} | {tx.transaction_date.strftime('%b %d %H:%M')} | "
                      f"{tx.get_transaction_type_display():<25} | "
                      f"{direction_symbol}K{tx.amount:>9,.2f}")
            print(f"  💡 These transactions might not be counted in vault balances!")
        else:
            print(f"    ✅ All transactions have vault_type assigned")
        
        # Find the discrepancy
        print(f"\n🔍 DISCREPANCY ANALYSIS:")
        
        # Get month closing
        month_closing = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_type='month_close',
            transaction_date__gte=june_start
        ).order_by('transaction_date').first()
        
        if month_closing:
            opening_balance = month_closing.amount
            opening_date = month_closing.transaction_date
            
            print(f"  Opening Balance: K{opening_balance:,.2f} (from {opening_date.strftime('%b %d %H:%M')})")
            
            # Calculate from all transactions after opening
            all_txs = VaultTransaction.objects.filter(
                branch__iexact=branch.name,
                transaction_date__gt=opening_date
            ).exclude(transaction_type='month_close')
            
            totals = all_txs.aggregate(
                inflows=Sum('amount', filter=Q(direction='in')),
                outflows=Sum('amount', filter=Q(direction='out'))
            )
            
            total_in = totals['inflows'] or Decimal('0')
            total_out = totals['outflows'] or Decimal('0')
            net_change = total_in - total_out
            
            expected_balance = opening_balance + net_change
            actual_balance = (daily_vault.balance if daily_vault else Decimal('0')) + (weekly_vault.balance if weekly_vault else Decimal('0'))
            difference = actual_balance - expected_balance
            
            print(f"  June Inflows:  +K{total_in:,.2f}")
            print(f"  June Outflows: -K{total_out:,.2f}")
            print(f"  June Net:       K{net_change:,.2f}")
            print(f"  ")
            print(f"  Expected Balance: K{expected_balance:,.2f} (opening + net)")
            print(f"  Actual Balance:   K{actual_balance:,.2f}")
            print(f"  Difference:       K{difference:,.2f}")
            
            if abs(difference) < Decimal('0.01'):
                print(f"  ✅ BALANCED - No discrepancy")
            else:
                print(f"  ⚠️  DISCREPANCY: K{abs(difference):,.2f} {'missing' if difference < 0 else 'extra'}")
                
                # Try to find the cause
                print(f"\n  🔎 Possible causes:")
                
                # Check if month closing was recorded as OUT instead of IN
                if month_closing.direction == 'out':
                    print(f"    • Month closing is OUT (removing balance) instead of IN (bringing forward)")
                    print(f"      This would cause K{opening_balance * 2:,.2f} discrepancy")
                
                # Check for transactions without vault_type
                if null_count > 0:
                    null_totals = VaultTransaction.objects.filter(
                        branch__iexact=branch.name,
                        vault_type__isnull=True,
                        transaction_date__gt=opening_date
                    ).aggregate(
                        inflows=Sum('amount', filter=Q(direction='in')),
                        outflows=Sum('amount', filter=Q(direction='out'))
                    )
                    null_in = null_totals['inflows'] or Decimal('0')
                    null_out = null_totals['outflows'] or Decimal('0')
                    null_net = null_in - null_out
                    
                    if abs(null_net) > Decimal('0'):
                        print(f"    • {null_count} transactions without vault_type")
                        print(f"      Net impact: K{null_net:,.2f}")
                        print(f"      These might not be reflected in vault balances")
                
                # Check DailyVault vs WeeklyVault distribution
                daily_txs_sum = VaultTransaction.objects.filter(
                    branch__iexact=branch.name,
                    vault_type='daily',
                    transaction_date__gt=opening_date
                ).aggregate(
                    inflows=Sum('amount', filter=Q(direction='in')),
                    outflows=Sum('amount', filter=Q(direction='out'))
                )
                
                daily_in = daily_txs_sum['inflows'] or Decimal('0')
                daily_out = daily_txs_sum['outflows'] or Decimal('0')
                daily_net = daily_in - daily_out
                
                if daily_net != Decimal('0') and (not daily_vault or daily_vault.balance == 0):
                    print(f"    • Daily vault has K{daily_net:,.2f} worth of transactions")
                    print(f"      But DailyVault model shows K{daily_vault.balance if daily_vault else 0:,.2f}")
                    print(f"      Discrepancy: K{daily_net - (daily_vault.balance if daily_vault else Decimal('0')):,.2f}")
        
        else:
            print(f"  ❌ No month closing found - cannot calculate expected balance")
    
    print(f"\n{'═' * 80}")
    print()
    print("SUMMARY:")
    print("--------")
    print()
    print("1. DAILY VAULT USAGE:")
    print("   All branches show K0 in Daily Vault because:")
    
    daily_usage_count = 0
    for branch in branches:
        count = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            vault_type='daily',
            transaction_date__gte=june_start
        ).count()
        if count > 0:
            daily_usage_count += 1
    
    if daily_usage_count == 0:
        print("   ❌ NO BRANCHES are using Daily Vault for transactions")
        print("   💡 All operations are going to Weekly Vault")
        print("   💡 This is fine if they only do weekly loans")
    else:
        print(f"   ✅ {daily_usage_count} branch(es) are using Daily Vault")
    
    print()
    print("2. MISSING MONEY:")
    print("   Discrepancies exist because:")
    print("   • Opening balances might have been recorded as OUT (removing) instead of IN")
    print("   • Some transactions might not have vault_type assigned")
    print("   • Vault model balances might not be synced with transactions")
    print()
    print("RECOMMENDATIONS:")
    print("----------------")
    print("✅ If branches only do weekly loans: Daily Vault at K0 is normal")
    print("⚠️  If branches do daily loans: Need to route those transactions to Daily Vault")
    print("🔧 To fix discrepancies: Run recalculate_all_vault_balances.py")
    print()
    print("=" * 80)

if __name__ == '__main__':
    investigate()
