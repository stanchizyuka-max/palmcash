#!/usr/bin/env python
"""
Safely remove old BranchVault data after migration to dual vault system

This script:
1. Verifies all transactions have vault_type set
2. Creates a backup of old BranchVault data
3. Removes old BranchVault records
4. Confirms the dual vault system is working correctly
"""
import os
import django
import json
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import BranchVault, DailyVault, WeeklyVault
from expenses.models import VaultTransaction
from clients.models import Branch
from decimal import Decimal

def cleanup_old_branchvault():
    print("=" * 70)
    print("OLD BRANCHVAULT CLEANUP SCRIPT")
    print("=" * 70)
    print("\nThis script will safely remove the deprecated BranchVault data.")
    print("All data will be backed up before deletion.\n")
    
    # Step 1: Verify all transactions have vault_type
    print("Step 1: Verifying all transactions have vault_type...")
    print("-" * 70)
    
    missing_vault_type = VaultTransaction.objects.filter(
        vault_type__isnull=True
    ) | VaultTransaction.objects.filter(vault_type='')
    
    if missing_vault_type.exists():
        print(f"❌ ERROR: Found {missing_vault_type.count()} transactions without vault_type!")
        print("\nPlease run fix_vault_data.py first to assign vault_type to all transactions.")
        print("\nTransactions without vault_type:")
        for tx in missing_vault_type[:10]:  # Show first 10
            print(f"  - {tx.branch} | {tx.transaction_date.date()} | {tx.get_transaction_type_display()}")
        if missing_vault_type.count() > 10:
            print(f"  ... and {missing_vault_type.count() - 10} more")
        return False
    
    print("✓ All transactions have vault_type assigned")
    
    # Step 2: Create backup of old BranchVault data
    print("\nStep 2: Creating backup of old BranchVault data...")
    print("-" * 70)
    
    old_vaults = BranchVault.objects.all()
    
    if not old_vaults.exists():
        print("✓ No old BranchVault records found - already cleaned up!")
        return True
    
    backup_data = []
    for vault in old_vaults:
        backup_data.append({
            'branch_id': vault.branch.id,
            'branch_name': vault.branch.name,
            'balance': str(vault.balance),
            'created_at': vault.created_at.isoformat() if vault.created_at else None,
            'updated_at': vault.updated_at.isoformat() if vault.updated_at else None,
        })
    
    # Save backup to file
    backup_filename = f'branchvault_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(backup_filename, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"✓ Backed up {len(backup_data)} BranchVault records to {backup_filename}")
    
    # Show what will be deleted
    print("\nOld BranchVault records to be removed:")
    for vault in old_vaults:
        print(f"  - {vault.branch.name}: K{vault.balance:,.2f}")
    
    # Step 3: Verify dual vault system is working
    print("\nStep 3: Verifying dual vault system...")
    print("-" * 70)
    
    branches = Branch.objects.filter(is_active=True)
    all_good = True
    
    for branch in branches:
        # Check if branch has transactions
        has_txs = VaultTransaction.objects.filter(branch=branch.name).exists()
        
        if has_txs:
            # Check if dual vaults exist
            has_daily = DailyVault.objects.filter(branch=branch).exists()
            has_weekly = WeeklyVault.objects.filter(branch=branch).exists()
            
            if not has_daily and not has_weekly:
                print(f"⚠️  {branch.name}: Has transactions but no dual vaults!")
                all_good = False
            else:
                daily_bal = DailyVault.objects.filter(branch=branch).first()
                weekly_bal = WeeklyVault.objects.filter(branch=branch).first()
                daily_amount = daily_bal.balance if daily_bal else Decimal('0')
                weekly_amount = weekly_bal.balance if weekly_bal else Decimal('0')
                total = daily_amount + weekly_amount
                print(f"✓ {branch.name}: Daily K{daily_amount:,.2f} + Weekly K{weekly_amount:,.2f} = K{total:,.2f}")
    
    if not all_good:
        print("\n❌ Some branches have issues with dual vault setup!")
        print("Please run fix_vault_data.py first.")
        return False
    
    print("\n✓ All branches have proper dual vault setup")
    
    # Step 4: Confirm deletion
    print("\n" + "=" * 70)
    print("READY TO DELETE OLD BRANCHVAULT RECORDS")
    print("=" * 70)
    print(f"\nBackup saved to: {backup_filename}")
    print(f"Records to delete: {old_vaults.count()}")
    print("\nThis action will:")
    print("  1. Delete all BranchVault records")
    print("  2. Keep the backup file for safety")
    print("  3. Not affect any VaultTransaction records")
    print("  4. Not affect DailyVault or WeeklyVault records")
    
    response = input("\nProceed with deletion? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Deletion cancelled by user")
        return False
    
    # Step 5: Delete old BranchVault records
    print("\nStep 5: Deleting old BranchVault records...")
    print("-" * 70)
    
    count = old_vaults.count()
    old_vaults.delete()
    
    print(f"✓ Deleted {count} old BranchVault records")
    
    # Step 6: Verify deletion
    print("\nStep 6: Verifying deletion...")
    print("-" * 70)
    
    remaining = BranchVault.objects.all().count()
    if remaining == 0:
        print("✓ All old BranchVault records successfully removed")
    else:
        print(f"⚠️  Warning: {remaining} BranchVault records still exist")
    
    # Final summary
    print("\n" + "=" * 70)
    print("CLEANUP COMPLETE")
    print("=" * 70)
    print("\nSummary:")
    print(f"  ✓ Backed up {count} records to {backup_filename}")
    print(f"  ✓ Deleted {count} old BranchVault records")
    print(f"  ✓ Dual vault system verified and working")
    print("\nThe system is now using only the dual vault system (DailyVault + WeeklyVault).")
    print("All future transactions will use the correct vault system.")
    
    return True

if __name__ == '__main__':
    try:
        success = cleanup_old_branchvault()
        if success:
            print("\n✅ Cleanup successful!")
        else:
            print("\n⚠️  Cleanup not completed - please review the messages above")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
