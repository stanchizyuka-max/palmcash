#!/usr/bin/env python
"""
Fix the WeeklyVault balance for KAMWALA SOUTH
The vault transaction was created but the vault balance wasn't updated
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import WeeklyVault
from expenses.models import VaultTransaction
from clients.models import Branch
from decimal import Decimal

print("\n" + "="*70)
print("FIX VAULT BALANCE FOR KAMWALA SOUTH")
print("="*70)

# Get the branch
branch = Branch.objects.filter(name__iexact='KAMWALA SOUTH').first()
if not branch:
    print("\n❌ KAMWALA SOUTH branch not found!")
    exit()

print(f"\n✅ Found branch: {branch.name}")

# Get the weekly vault
vault, created = WeeklyVault.objects.get_or_create(branch=branch)

print(f"\n📊 CURRENT VAULT STATUS:")
print(f"Current balance: K{vault.balance}")
print(f"Total inflows:   K{vault.total_inflows}")
print(f"Total outflows:  K{vault.total_outflows}")

# Get Inonge's vault transaction
inonge_tx = VaultTransaction.objects.filter(
    branch__iexact='KAMWALA SOUTH',
    vault_type='weekly',
    loan__application_number='LV-000035',
    transaction_type='loan_disbursement',
    direction='out'
).first()

if not inonge_tx:
    print("\n❌ Inonge's vault transaction not found!")
    exit()

print(f"\n✅ Found Inonge's transaction:")
print(f"Transaction ID:  {inonge_tx.id}")
print(f"Amount:          K{inonge_tx.amount}")
print(f"Balance After:   K{inonge_tx.balance_after}")
print(f"Date:            {inonge_tx.transaction_date}")

# The transaction says balance should be K1,273 after the K3,000 disbursement
# Current balance is K4,273
# So we need to deduct K3,000

expected_balance = inonge_tx.balance_after
amount_to_deduct = inonge_tx.amount

print(f"\n🔍 ANALYSIS:")
print(f"Current vault balance:     K{vault.balance}")
print(f"Amount to deduct:          K{amount_to_deduct}")
print(f"Expected balance:          K{expected_balance}")
print(f"Difference:                K{vault.balance - expected_balance}")

if vault.balance == expected_balance:
    print(f"\n✅ Vault balance is already correct!")
    print(f"Nothing to fix.")
    exit()

# Update the vault balance
print(f"\n🔄 Updating vault balance...")

from django.db import transaction

try:
    with transaction.atomic():
        # Deduct the amount
        vault.balance -= amount_to_deduct
        vault.total_outflows += amount_to_deduct
        vault.save(update_fields=['balance', 'total_outflows', 'updated_at'])
        
        print(f"\n✅ SUCCESS! Vault balance updated!")
        print(f"\nNEW VAULT STATUS:")
        print(f"Balance:         K{vault.balance}")
        print(f"Total inflows:   K{vault.total_inflows}")
        print(f"Total outflows:  K{vault.total_outflows}")
        
        if vault.balance == expected_balance:
            print(f"\n✅ Balance now matches transaction record: K{expected_balance}")
        else:
            print(f"\n⚠️  Warning: Balance K{vault.balance} doesn't match expected K{expected_balance}")

except Exception as e:
    print(f"\n❌ Error updating vault balance: {e}")
    import traceback
    traceback.print_exc()
    exit()

print("\n" + "="*70)
print("DONE - VAULT BALANCE FIXED")
print("="*70)

print("\n💡 WHAT WAS FIXED:")
print(f"  ✅ Deducted K{amount_to_deduct} from weekly vault")
print(f"  ✅ Updated balance from K{vault.balance + amount_to_deduct} to K{vault.balance}")
print(f"  ✅ Updated total outflows")

print("\n📊 VERIFICATION:")
print("  1. Refresh the vault dashboard")
print("  2. Weekly vault should now show K1,273.00")
print("  3. Total balance should be K8,183.00 (K6,910 + K1,273)")

print("\n" + "="*70 + "\n")

