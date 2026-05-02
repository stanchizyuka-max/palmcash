# Vault Balance Calculation Bug - Fix Documentation

## Problem Summary

The vault balance calculations were **completely wrong** due to a critical bug where different parts of the system were updating different vault models.

### What Was Wrong

1. **Mixed Vault Systems**: The system has two vault models:
   - **OLD**: `BranchVault` (single vault, deprecated)
   - **NEW**: `DailyVault` and `WeeklyVault` (dual vault system)

2. **Inconsistent Updates**:
   - ✅ Capital injections → Updated NEW dual vault system
   - ✅ Bank withdrawals → Updated NEW dual vault system
   - ❌ **Expenses** → Updated OLD single vault system
   - ❌ **Payment collections** → Updated OLD single vault system
   - ❌ **Manual collections** → Updated OLD single vault system

3. **Result**: 
   - Transactions were recorded in `VaultTransaction` table
   - But the actual vault balances were split across two different database tables
   - The displayed balance was from the NEW system, but expenses/collections were updating the OLD system
   - This caused completely incorrect balances (even negative balances!)

### Example from Your Data

Looking at your Kamwala south branch:
- **Total Inflows**: K7,540.00 (K2,180 + K2,180 + K2,180 + K1,000)
- **Total Outflows**: K1,910.00 (K1,540 + K310 + K30 + K30)
- **Expected Balance**: K5,630.00
- **Actual Displayed**: K-1,540.00 ❌ **WRONG!**

The balance was negative because:
1. Capital injection (K1,000) went to WeeklyVault
2. Payment collections (K6,540) went to OLD BranchVault
3. Expenses (K370) went to OLD BranchVault
4. Bank deposit (K1,540) went to WeeklyVault
5. Display showed WeeklyVault balance: K1,000 - K1,540 = K-1,540

## What Was Fixed

### Code Changes

1. **expenses/views.py** (Line ~101)
   - Changed from `BranchVault` to `WeeklyVault`
   - Added `vault_type='weekly'` to transactions
   - Added proper vault field updates (last_transaction_date, total_outflows)

2. **dashboard/views.py** (Line ~3071)
   - Changed from `BranchVault` to `WeeklyVault`
   - Added `vault_type='weekly'` to transactions
   - Added proper vault field updates

3. **payments/views.py** (Line ~1055)
   - Changed from `BranchVault` to dual vault system
   - Determines vault type from loan type (daily vs weekly)
   - Routes collections to correct vault
   - Added proper vault field updates

4. **dashboard/vault_views.py** (Line ~389)
   - Changed manual collection from `BranchVault` to dual vault system
   - Added vault_type parameter
   - Added proper vault field updates

5. **dashboard/templates/dashboard/vault_collection.html**
   - Added vault type selector dropdown
   - Allows choosing between daily and weekly vault for collections

## How to Fix Your Data

### Step 1: Run the Data Fix Script

```bash
python fix_vault_data.py
```

This script will:
1. Set `vault_type` for all existing transactions that don't have it
2. Recalculate all `balance_after` values in chronological order
3. Update DailyVault and WeeklyVault balances to match the transaction history

### Step 2: Verify the Fix

1. Go to the vault page for Kamwala south
2. Check that the balance now shows **K5,630.00** (or close to it)
3. Verify that the "Balance After" column makes sense when reading from bottom to top

### Step 3: Going Forward

From now on:
- All new expenses will go to the weekly vault
- All new collections will go to the appropriate vault (daily or weekly based on loan type)
- Manual collections will ask you which vault to use
- Capital injections already work correctly

## Technical Details

### Database Tables Involved

1. **expenses_vaulttransaction**: Records all transactions (this was working correctly)
2. **loans_branchvault**: OLD single vault (was being updated incorrectly)
3. **loans_dailyvault**: NEW daily vault (now being updated correctly)
4. **loans_weeklyvault**: NEW weekly vault (now being updated correctly)

### Transaction Types and Default Vaults

| Transaction Type | Default Vault | Notes |
|-----------------|---------------|-------|
| Capital Injection | User selects | Admin chooses daily or weekly |
| Bank Withdrawal | User selects | Manager/admin chooses |
| Bank Deposit | User selects | Manager/admin chooses |
| Fund Received | User selects | Manager/admin chooses |
| Branch Transfer | User selects | Manager/admin chooses |
| Expense | Weekly | Expenses typically from weekly vault |
| Payment Collection | Loan-based | Daily loans → daily vault, Weekly loans → weekly vault |
| Manual Collection | User selects | Manager/admin chooses |
| Security Deposit | Loan-based | Follows loan type |
| Loan Disbursement | Loan-based | Follows loan type |
| Security Return | Loan-based | Follows loan type |

## Prevention

To prevent this from happening again:

1. **Never use `BranchVault`** - it's deprecated
2. **Always specify `vault_type`** when creating VaultTransaction records
3. **Always update the correct vault model** (DailyVault or WeeklyVault)
4. **Always update these fields** when modifying vault:
   - `balance`
   - `last_transaction_date`
   - `total_inflows` (for inflows)
   - `total_outflows` (for outflows)
   - `updated_at` (automatically updated)

## Testing Checklist

After running the fix script, test these scenarios:

- [ ] Create a new expense - verify it deducts from weekly vault
- [ ] Record a payment collection - verify it goes to correct vault based on loan type
- [ ] Record a manual collection - verify you can choose vault type
- [ ] Inject capital - verify it goes to selected vault
- [ ] Check vault balance matches sum of transactions
- [ ] Export CSV and verify totals match displayed totals

## Questions?

If you see any issues after running the fix:
1. Check the script output for errors
2. Verify your database connection is working
3. Make sure all migrations are applied: `python manage.py migrate`
4. Contact support if balances still don't match
