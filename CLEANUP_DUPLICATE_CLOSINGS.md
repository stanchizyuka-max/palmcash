# Cleanup Duplicate Month Closings

## Problem
You accidentally closed April 2026 three times, creating duplicate closing transactions.

## Solution

### Step 1: Preview What Will Be Deleted (Dry Run)
```bash
python manage.py cleanup_duplicate_closings --dry-run
```

This will show you:
- Which closings will be KEPT (the first one)
- Which closings will be DELETED (duplicates)

### Step 2: Actually Delete the Duplicates
```bash
python manage.py cleanup_duplicate_closings
```

This will:
- Keep the first closing for April 2026 (K6,689.91 at 6:17 AM with reference CLOSE-2026-04-DEE2)
- Delete the 2 duplicate closings (6:17 AM and 6:28 AM)

### Step 3: Verify
After cleanup, check:
1. **Vault History** - Should show only 1 closing for April 2026
2. **Vault Dashboard** - Should show correct balance

## Prevention
The system now prevents closing the same month twice. If you try to close April 2026 again, you'll get an error message:
> "Month 2026-04 has already been closed. You cannot close the same month twice."

## Expected Result After Cleanup

**Before:**
- 3 closings for April 2026
- Total outflows: K20,069.73 (K6,689.91 × 3)

**After:**
- 1 closing for April 2026
- Correct transaction history
- Vault balance: K0.00 (as expected after closing)

## Notes
- The cleanup command is safe - it only removes duplicate month_close transactions
- Regular transactions (collections, disbursements, etc.) are not affected
- You can run it for a specific branch: `python manage.py cleanup_duplicate_closings --branch MANDEVU`
