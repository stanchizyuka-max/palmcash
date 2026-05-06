# MANDEVU BRANCH Data Recovery Instructions

## Issue Summary
After renaming "MANDEVU BRANCJ" to "MANDEVU BRANCH", the branch shows:
- ✅ 22 Vault Transactions (visible)
- ❌ 0 Officer Assignments
- ❌ 0 Borrower Groups
- ❌ 0 Loans

## Root Cause
The `OfficerAssignment.branch` field stores branch names as **strings** (CharField), not as references to Branch objects. When you renamed the branch in the admin panel, it only updated the Branch table, but didn't update the string references in OfficerAssignment.

## Solution

### Step 1: Pull Latest Code
```bash
cd ~/www/palmcashloans.site
git pull origin main
```

### Step 2: Run the Fixed Restoration Script
```bash
python restore_mandevu_data.py
```

### What the Script Does
The script will:
1. ✅ Check current state of MANDEVU BRANCH
2. ✅ Look for references to old name "MANDEVU BRANCJ"
3. ✅ Show all officer assignments in the system
4. ✅ Show all borrower groups in the system
5. ✅ Update officer assignments from old name to new name
6. ✅ Update vault transactions (if any still have old name)
7. ✅ Update manager assignments
8. ✅ Update loans, vaults, and savings records

### Expected Output
```
================================================================================
MANDEVU BRANCH DATA RESTORATION
================================================================================
✓ Found branch: MANDEVU BRANCH (ID: 12)

--------------------------------------------------------------------------------
CHECKING CURRENT STATE
--------------------------------------------------------------------------------
Officer Assignments: 0
Borrower Groups: 0
Loans: 0
Vault Transactions: 22

--------------------------------------------------------------------------------
CHECKING FOR OLD NAME REFERENCES
--------------------------------------------------------------------------------
Vault Transactions with old name: 0
Officer Assignments with old name: X  ← Should find some here
Groups for this branch: X

--------------------------------------------------------------------------------
ALL OFFICER ASSIGNMENTS IN SYSTEM
--------------------------------------------------------------------------------
Total: 14
  - Officer Name → MANDEVU BRANCJ  ← These will be updated
  - Officer Name → Other Branch
  ...

================================================================================
STARTING DATA MIGRATION
================================================================================
✓ Updated X officer assignments
✓ Updated X vault transactions
...

================================================================================
VERIFICATION
================================================================================
MANDEVU BRANCH now has:
  - Officer Assignments: X  ← Should show officers now
  - Borrower Groups: X
  - Vault Transactions: 22
```

### Step 3: Verify in Admin Panel
1. Go to **Admin Dashboard** → **Branches**
2. Find **MANDEVU BRANCH**
3. Check that "Officers" column now shows the correct count
4. Click "View" to see branch details
5. Verify officers, groups, and loans are visible

## If Data Was Actually Deleted

If the script shows **0 officer assignments with old name**, it means the data was actually deleted (not just renamed). In this case:

### Manual Recovery Steps

1. **Check if officers exist but are unassigned:**
   - Go to Admin → Manage Users
   - Look for loan officers without branch assignments
   - Manually assign them to MANDEVU BRANCH

2. **Check if groups exist but are unlinked:**
   - Go to Admin → Groups
   - Look for groups without branch assignments
   - Manually assign them to MANDEVU BRANCH

3. **If data is truly lost:**
   - You'll need to restore from a database backup
   - Or manually recreate officer assignments and groups

## Prevention for Future

**IMPORTANT:** When renaming a branch in the future:

1. ❌ **DON'T** just edit the branch name in the admin panel
2. ✅ **DO** use a migration script that updates all related records
3. ✅ **DO** create a database backup before making changes
4. ✅ **DO** test the rename on a staging environment first

## Alternative: Use Branch Code Instead

Consider using the **Branch Code** field for system references instead of the branch name:
- Branch codes don't change (e.g., "04" for MANDEVU)
- Names can be updated without breaking references
- More stable for database relationships

## Need Help?

If the script doesn't fix the issue:
1. Share the complete output of `python restore_mandevu_data.py`
2. Check if there's a database backup from before the rename
3. We can write a more targeted recovery script based on what data exists

## Summary

The issue is that officer assignments store branch names as strings. The fix updates all string references from "MANDEVU BRANCJ" to "MANDEVU BRANCH". Run the script and the data should be restored!
