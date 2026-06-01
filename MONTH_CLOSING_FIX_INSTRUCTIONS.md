# Month Closing Fix Instructions

## Current Situation
After closing months for all branches, some figures are still showing:
- ✅ Vault balances: K0.00 (CORRECT)
- ❌ Savings balances: Still showing amounts (KUKU: K7,150)
- ❌ Security deposits: Still showing amounts (Chazanga: K9,600, KAMWALA: K4,200, KUKU: K10,700, MANDEVU: K6,500)
- ⚠️  Inflows/Outflows: Showing month closing transactions (legitimate but may look confusing)

## Why This Happened
The month closings were done BEFORE the latest code was deployed. The old code didn't properly reset:
1. Savings balances
2. Security deposits (which come from vault transactions, not the SecurityDeposit model)

## Fixes Applied

### 1. Fixed Logger Error ✅
**File:** `dashboard/vault_views.py`
**Issue:** `UnboundLocalError: cannot access local variable 'logger'`
**Fix:** Moved logger initialization to the top of the function before it's used

### 2. Created Diagnostic Scripts ✅

#### Script 1: `check_current_vault_state.py`
**Purpose:** Shows current state of all branches - what's at K0.00 and what's not
**Usage:**
```bash
cd ~/www/palmcashloans.site
source .venv/bin/activate
python check_current_vault_state.py
```

#### Script 2: `fix_remaining_month_close_issues.py`
**Purpose:** Resets all BranchSavings balances to K0.00 and verifies vault counters
**Usage:**
```bash
python fix_remaining_month_close_issues.py
```

#### Script 3: `reset_security_deposits_after_month_close.py`
**Purpose:** Creates security_return transactions to bring all security balances to K0.00
**Usage:**
```bash
python reset_security_deposits_after_month_close.py
```
**⚠️ WARNING:** This creates vault transactions. Only run if you want to zero out ALL security deposits.

## Step-by-Step Fix Process

### Step 1: Check Current State
```bash
cd ~/www/palmcashloans.site
source .venv/bin/activate
python check_current_vault_state.py
```
This will show you exactly what needs to be fixed.

### Step 2: Fix Savings Balances
```bash
python fix_remaining_month_close_issues.py
```
This will:
- Reset all BranchSavings balances to K0.00
- Verify vault inflows/outflows are correct
- Report on security deposits

### Step 3: Fix Security Deposits (OPTIONAL)
**⚠️ IMPORTANT:** Only run this if you want to zero out ALL security deposits!

Security deposits are calculated from vault transactions:
- Security IN: All `security_deposit` transactions (direction='in')
- Security OUT: All `security_return` and `security_used` transactions (direction='out')
- Balance: IN - OUT

If you want to reset these to K0.00:
```bash
python reset_security_deposits_after_month_close.py
```

This will create `security_return` transactions for each branch to bring the balance to K0.00.

**Alternative:** If these security deposits are legitimate and should remain, leave them as is.

### Step 4: Deploy Code Changes
```bash
# Pull latest code
git pull origin main

# Restart the application
sudo systemctl restart palmcash  # or whatever your service name is
```

### Step 5: Hard Refresh Browser
**CRITICAL:** After all fixes, users MUST hard refresh their browser:
- **Windows/Linux:** Ctrl + Shift + R
- **Mac:** Cmd + Shift + R

This clears the browser cache and loads the latest data.

## Understanding the Numbers

### Inflows/Outflows
The vault page now has **auto-filtering** - when no date filter is set, it automatically shows only transactions AFTER the last month closing. This means:
- Inflows/Outflows counters show current month activity only
- Month closing transactions appear in the list but are excluded from the auto-filter
- This is CORRECT behavior - it prevents cumulative totals from showing

### Security Deposits
Security deposits are NOT stored in the `SecurityDeposit.paid_amount` field for vault purposes. They are calculated from vault transactions:
- When a security deposit is paid → `security_deposit` transaction (IN)
- When security is returned → `security_return` transaction (OUT)
- Balance = Total IN - Total OUT

This is why the `reset_all_securities_simple.py` script didn't work - it was looking in the wrong place.

## What Each Branch Should Show After Fixes

| Branch | Daily Vault | Weekly Vault | Savings | Security | Inflows | Outflows |
|--------|-------------|--------------|---------|----------|---------|----------|
| Chazanga | K0.00 | K0.00 | K0.00 | K0.00* | K0.00** | K0.00** |
| KAMWALA SOUTH | K0.00 | K0.00 | K0.00 | K0.00* | K0.00** | K0.00** |
| KUKU | K0.00 | K0.00 | K0.00 | K0.00* | K0.00** | K0.00** |
| MANDEVU | K0.00 | K0.00 | K0.00 | K0.00* | K0.00** | K0.00** |

\* Only if you run `reset_security_deposits_after_month_close.py`
\*\* Unless there are legitimate transactions after the month closing

## Troubleshooting

### Issue: Figures still showing after running scripts
**Solution:** Hard refresh browser (Ctrl + Shift + R)

### Issue: Security deposits not resetting
**Cause:** Security deposits come from vault transactions, not the SecurityDeposit model
**Solution:** Run `reset_security_deposits_after_month_close.py` to create return transactions

### Issue: Inflows/Outflows showing amounts
**Check:** Are these from transactions AFTER the month closing?
- If YES: This is correct - these are current month transactions
- If NO: Check the auto-filter logic in `vault_views.py`

### Issue: Month closing transactions showing in totals
**Expected:** Month closing transactions appear in the transaction list but should be excluded from filtered totals
**Check:** The auto-filter should exclude them when no date filter is set

## Future Month Closings

The current code (after today's fixes) will properly reset everything when you close a month:
1. ✅ Daily Vault balance → K0.00
2. ✅ Weekly Vault balance → K0.00
3. ✅ Savings balance → K0.00
4. ✅ Security deposits → K0.00 (via transaction)
5. ✅ Inflows counter → K0.00
6. ✅ Outflows counter → K0.00

The auto-filter will then show only transactions after the closing date.

## Questions?

If you have questions or issues:
1. Run `check_current_vault_state.py` to see the current state
2. Check the transaction history in the vault page
3. Verify the last month closing date for each branch
4. Ensure users have hard refreshed their browsers
