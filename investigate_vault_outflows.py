#!/usr/bin/env python
"""
Investigate what OUTFLOW transactions exist in the vault.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from datetime import date

def main():
    print("=" * 80)
    print("INVESTIGATING VAULT OUTFLOW TRANSACTIONS")
    print("=" * 80)
    
    today = date(2026, 6, 1)
    
    # Get all transactions for June 1, 2026
    all_tx = VaultTransaction.objects.filter(
        transaction_date__date=today
    ).order_by('branch', 'vault_type', 'transaction_date')
    
    print(f"\nTotal transactions for June 1, 2026: {all_tx.count()}")
    
    # Group by branch and vault type
    branches = {}
    
    for tx in all_tx:
        key = f"{tx.branch} - {tx.vault_type.upper()}"
        if key not in branches:
            branches[key] = {
                'inflows': [],
                'outflows': [],
            }
        
        if tx.direction == 'in':
            branches[key]['inflows'].append(tx)
        else:
            branches[key]['outflows'].append(tx)
    
    # Display results
    for branch_vault, data in sorted(branches.items()):
        print("\n" + "=" * 80)
        print(f"📍 {branch_vault}")
        print("=" * 80)
        
        print(f"\n✅ INFLOWS ({len(data['inflows'])} transactions):")
        inflow_total = 0
        for tx in data['inflows']:
            inflow_total += tx.amount
            print(f"   #{tx.id:4d} | {tx.transaction_date.strftime('%H:%M:%S')} | "
                  f"{tx.get_transaction_type_display():30s} | K{tx.amount:>10,.2f} | Ref: {tx.reference_number}")
        print(f"   TOTAL INFLOWS: K{inflow_total:,.2f}")
        
        print(f"\n❌ OUTFLOWS ({len(data['outflows'])} transactions):")
        outflow_total = 0
        for tx in data['outflows']:
            outflow_total += tx.amount
            print(f"   #{tx.id:4d} | {tx.transaction_date.strftime('%H:%M:%S')} | "
                  f"{tx.get_transaction_type_display():30s} | K{tx.amount:>10,.2f} | Ref: {tx.reference_number}")
            if tx.loan:
                print(f"          └─ Loan: {tx.loan.application_number}")
            if tx.payment:
                print(f"          └─ Payment: #{tx.payment.id}")
        print(f"   TOTAL OUTFLOWS: K{outflow_total:,.2f}")
        
        net = inflow_total - outflow_total
        print(f"\n   NET BALANCE: K{net:,.2f} {'✅' if net >= 0 else '❌ NEGATIVE!'}")
    
    print("\n" + "=" * 80)
    print("SUMMARY BY TRANSACTION TYPE")
    print("=" * 80)
    
    from django.db.models import Count, Sum
    
    by_type = all_tx.values('transaction_type', 'direction').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('transaction_type', 'direction')
    
    for item in by_type:
        tx_type = dict(VaultTransaction.TRANSACTION_TYPE_CHOICES).get(item['transaction_type'], item['transaction_type'])
        direction = 'IN' if item['direction'] == 'in' else 'OUT'
        print(f"   {tx_type:30s} | {direction:3s} | Count: {item['count']:3d} | Total: K{item['total']:>10,.2f}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
