# Vault Balance Issue - Explanation and Resolution

## 📋 What Happened

### Timeline of Events:

1. **May 31, 2026 (Before Month Closing)**
   - All branches had positive vault balances
   - Example: KUKU weekly vault had K16,233

2. **June 1, 2026 - Month Closing**
   - You closed the month for all branches
   - This reset all vaults to K0.00 (as requested)
   - Month closing transactions were created to record the amounts taken out

3. **June 1, 2026 - After Month Closing**
   - New transactions were made (payment collections, expenses, bank deposits)
   - **PROBLEM:** Payment collections are showing as OUT (outflow) instead of IN (inflow)
   - This caused vault balances to go negative

### Current State (BROKEN):

| Branch | Daily Vault | Weekly Vault | Total | Issue |
|--------|-------------|--------------|-------|-------|
| KAMWALA SOUTH | K-7,405 | K-2,120 | K-9,525 | Payment collections are OUT instead of IN |
| Chazanga | K8,006 | K980 | K8,986 | Has capital injection (shouldn't be there) |
| KUKU | K-7,805 | K-16,233 | K-24,038 | Severely negative - payment collections are OUT |
| MANDEVU | K0 | K0 | K0 | May have hidden issues |

### The Root Cause:

**Payment collections are being recorded with direction OUT instead of IN.**

When a borrower makes a payment:
- ✅ **Correct:** Direction = IN (money coming into vault)
- ❌ **Current:** Direction = OUT (money going out of vault)

This is backwards and causes negative balances.

---

## 🔍 Why This Happened

Looking at your screenshots, I can see:
- Payment collections show "▼ OUT" instead of "▲ IN"
- The amounts are being subtracted from the vault instead of added
- This happened after the month closing fix scripts were run

**Possible causes:**
1. The `fix_month_closing_amounts.py` script may have accidentally changed payment directions
2. There may be a bug in the payment recording code
3. Someone may have manually reversed transactions

---

## ✅ The Solution

I've created three scripts to diagnose and fix this:

### 1. `check_actual_state.py` - Diagnostic Script
**Purpose:** Shows exactly what's in the database right now

**What it shows:**
- Current vault model balances
- All transactions from June 1, 2026
- Direction of each transaction (IN or OUT)
- Whether there are REVERSAL transactions
- Calculated balances based on transactions

**Run this first to understand the problem.**

### 2. `fix_payment_collection_directions.py` - Fix Script
**Purpose:** Corrects payment collection directions and recalculates everything

**What it does:**
1. Finds all payment collections with direction OUT
2. Changes their direction to IN
3. Recalculates all balance_after values in chronological order
4. Updates vault model balances
5. Updates total inflows and outflows

**This is the main fix.**

### 3. `investigate_reversals.py` - Investigation Script
**Purpose:** Checks if transactions were manually reversed

**What it shows:**
- Transactions with "REVERSAL:" in description
- Who reversed them and when
- Payment collections with unusual OUT direction

**Run this if the fix doesn't work.**

---

## 📝 Step-by-Step Instructions

### On the Server:

```bash
# 1. Navigate to project
cd ~/www/palmcashloans.site

# 2. Pull latest code (includes the new scripts)
git pull origin main

# 3. Check current state
python check_actual_state.py
```

**Review the output carefully.** You should see:
- Payment collections with direction OUT (wrong!)
- Negative vault balances
- Transactions in chronological order

```bash
# 4. Run the fix
python fix_payment_collection_directions.py
```

Type `yes` when prompted.

**The script will:**
- Show each payment collection being fixed
- Recalculate all balances
- Display final balances for each branch

```bash
# 5. Verify the fix worked
python check_actual_state.py
```

**You should now see:**
- All payment collections with direction IN ✅
- All vault balances positive ✅
- No negative balances ✅

```bash
# 6. Restart the application
sudo systemctl restart palmcash
```

### On Your Computer:

1. **Hard refresh your browser:** Ctrl + Shift + R
2. **Check each branch vault page**
3. **Verify:**
   - All balances are positive or K0.00
   - Payment collections show "▲ IN" not "▼ OUT"
   - Total Inflows match the sum of all IN transactions
   - Balance After column flows correctly

---

## 🎯 Expected Results After Fix

### KAMWALA SOUTH:
- Payment collections will be IN instead of OUT
- Vault balance will be positive (sum of payment collections minus expenses)

### Chazanga:
- Daily vault: K0.00
- Weekly vault: K350 (K140 + K210 from payment collections)
- Total: K350

### KUKU:
- Payment collections will be IN instead of OUT
- Vault balance will be positive (sum of payment collections minus expenses)

### MANDEVU:
- Payment collections will be IN instead of OUT
- Vault balance will be positive

---

## ⚠️ Important Notes

1. **The fix is safe to run multiple times** - it only changes what needs to be changed

2. **No data will be lost** - we're only changing the direction field from 'out' to 'in'

3. **All users should hard refresh** after the fix is applied

4. **Capital injections will remain** - they were added by previous fix scripts and can be removed later if needed

5. **Month closing is correct** - the K0.00 reset is working as intended

---

## 🔧 If the Fix Doesn't Work

If after running the fix you still see issues:

1. Run `investigate_reversals.py` to check for REVERSAL transactions
2. Take screenshots of the vault pages
3. Run `check_actual_state.py` and save the output
4. Contact the developer with:
   - Screenshots
   - Output from check_actual_state.py
   - Description of what's still wrong

---

## 📞 Technical Details (For Developer)

### Database Changes Made:

```python
# For each payment_collection transaction with direction='out':
transaction.direction = 'in'  # Change OUT to IN
transaction.save()

# Then recalculate balance_after for all transactions:
running_balance = 0
for tx in transactions.order_by('transaction_date', 'id'):
    if tx.direction == 'in':
        running_balance += tx.amount
    else:
        running_balance -= tx.amount
    tx.balance_after = running_balance
    tx.save()

# Finally update vault models:
vault.balance = running_balance
vault.total_inflows = sum(inflow transactions)
vault.total_outflows = sum(outflow transactions)
vault.save()
```

### Why This Approach:

1. **Minimal changes** - only changes what's wrong (direction field)
2. **Preserves history** - doesn't delete any transactions
3. **Recalculates everything** - ensures consistency
4. **Safe to repeat** - idempotent operation

---

**Document Created:** June 1, 2026  
**Last Updated:** June 1, 2026  
**Status:** Ready for execution
