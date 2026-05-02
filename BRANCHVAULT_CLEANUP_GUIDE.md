# BranchVault Cleanup Guide

## Overview

The old `BranchVault` model has been deprecated in favor of the dual vault system (`DailyVault` and `WeeklyVault`). This guide explains how to safely remove the old data.

## Current Status

✅ **Code Updated**: All active code now uses the dual vault system  
⚠️ **Data Exists**: Old BranchVault records still exist in the database  
✅ **Safe to Remove**: Old data is no longer being used

## Why Remove Old BranchVault Data?

1. **Prevents Confusion**: Having two vault systems in the database is confusing
2. **Cleaner Database**: Removes deprecated tables and data
3. **Prevents Errors**: Ensures no code accidentally uses the old system
4. **Better Performance**: Fewer tables to query

## What Will Be Removed?

The `loans_branchvault` table contains old vault balance data that is no longer used. For example:
- Kamwala south: K6,170.00 (old, incorrect balance)
- Other branches: Various old balances

This data is **not being used** by the system anymore. The system now uses:
- `loans_dailyvault` - For daily loan operations
- `loans_weeklyvault` - For weekly loan operations

## How to Clean Up

### Step 1: Pull Latest Code

```bash
cd ~/www/palmcashloans.site
git pull origin main
```

### Step 2: Run the Cleanup Script

```bash
python cleanup_old_branchvault.py
```

The script will:
1. ✅ Verify all transactions have `vault_type` assigned
2. ✅ Create a backup JSON file of old BranchVault data
3. ✅ Verify the dual vault system is working correctly
4. ✅ Ask for confirmation before deleting
5. ✅ Delete old BranchVault records
6. ✅ Confirm deletion was successful

### Step 3: Review the Backup

The script creates a backup file like:
```
branchvault_backup_20260502_143022.json
```

This file contains all the old BranchVault data in case you ever need to reference it.

### Step 4: Verify Everything Works

1. Go to the vault page in your browser
2. Check that balances are correct
3. Try creating a new transaction (expense, collection, etc.)
4. Verify the transaction updates the correct vault

## What If Something Goes Wrong?

The cleanup script is designed to be safe:

1. **Backup Created**: All old data is backed up to a JSON file
2. **Verification First**: Script checks everything before deleting
3. **Confirmation Required**: You must type "yes" to proceed
4. **No Transaction Data Lost**: Only the old vault balance records are removed
5. **Dual Vaults Untouched**: DailyVault and WeeklyVault are not affected

If you need to restore the old data:
1. The backup JSON file contains all the old balances
2. Contact support with the backup file
3. We can restore if absolutely necessary (though it shouldn't be needed)

## Technical Details

### Tables Affected

**Removed:**
- `loans_branchvault` - Old single vault model (deprecated)

**Kept:**
- `loans_dailyvault` - New daily vault (active)
- `loans_weeklyvault` - New weekly vault (active)
- `expenses_vaulttransaction` - All transaction records (unchanged)

### Code Changes

**Files Updated:**
- `payments/views.py` - Removed BranchVault import
- `dashboard/views.py` - Updated to use dual vault balances
- `dashboard/vault_views.py` - Removed BranchVault references
- `dashboard/templates/dashboard/vault.html` - Updated to use branch object

**Still Using BranchVault:**
- `dashboard/vault_views.py` - `vault_month_close()` function
  - This function needs a separate update for dual vaults
  - For now, avoid using "Close Month" feature
  - Will be updated in a future release

## FAQ

### Q: Will this affect my transaction history?
**A:** No. All transaction records in `VaultTransaction` are preserved. Only the old vault balance records are removed.

### Q: What if I haven't run fix_kamwala_transactions.py yet?
**A:** The cleanup script will check and warn you if transactions are missing `vault_type`. Run the fix script first.

### Q: Can I undo the cleanup?
**A:** The backup JSON file contains all the old data. While you can't automatically restore it, the data is preserved for reference.

### Q: Will this affect the month closing feature?
**A:** The month closing feature still uses the old system and needs to be updated separately. Avoid using it until it's updated.

### Q: What happens to the BranchVault model in the code?
**A:** The model definition stays in `loans/models.py` for now (for migration compatibility), but no data will exist in the table.

## Next Steps After Cleanup

1. ✅ Old BranchVault data removed
2. ✅ System using only dual vault system
3. ⏳ Update month closing feature for dual vaults (future task)
4. ⏳ Remove BranchVault model definition (after confirming everything works)

## Support

If you encounter any issues:
1. Check the backup JSON file was created
2. Review the script output for error messages
3. Contact support with:
   - The backup JSON file
   - Screenshot of any errors
   - Description of what went wrong
