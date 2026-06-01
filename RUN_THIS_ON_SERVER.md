# 🚀 URGENT FIX - Run on Server (June 1, 2026)

## ⚠️ CURRENT PROBLEM:
Payment collections are showing as **OUT** (outflow) instead of **IN** (inflow), causing negative vault balances!

## Current Status:
- **KAMWALA SOUTH:** K-9,525 ❌ (payment collections reversed to OUT)
- **KUKU:** K-24,038 ❌ (payment collections reversed to OUT)
- **MANDEVU:** K0 ⚠️ (may have issues)
- **Chazanga:** K8,986 ⚠️ (has capital injection that shouldn't be there)

---

## 📋 COMPLETE FIX WORKFLOW:

### Step 1: Pull Latest Code
```bash
cd ~/www/palmcashloans.site
git pull origin main
```

This gets the new diagnostic and fix scripts.

---

### Step 2: Check Current State (Diagnostic)
```bash
python check_actual_state.py
```

**What to look for:**
- Payment collections with direction OUT (wrong!)
- Negative vault balances
- Capital injection transactions
- Security return transactions

**Save this output** - you'll compare it with the results after the fix.

---

### Step 3: Fix Payment Collection Directions
```bash
python fix_payment_collection_directions.py
```

Type `yes` when prompted.

**What it does:**
- Changes payment collection direction from OUT to IN
- Recalculates all balance_after values
- Updates vault model balances
- Updates inflows/outflows

**Expected output:**
- Shows each payment collection being fixed
- Shows balance recalculations
- Shows final balances for each branch

---

### Step 4: Verify the Fix
```bash
python check_actual_state.py
```

**You should now see:**
- ✅ All payment collections with direction IN (not OUT)
- ✅ All vault balances positive (no negatives)
- ⚠️ Capital injections and security returns still present (we'll remove these next)

---

### Step 5: Remove Capital Injections (Optional but Recommended)
```bash
python remove_capital_injections.py
```

Type `yes` when prompted (twice - once to confirm you ran step 3, once to confirm deletion).

**What it does:**
- Removes capital injection transactions added by previous fix scripts
- Removes security return transactions added by previous fix scripts
- Recalculates all balances
- Updates vault models

**Why remove them:**
- They were added to fix negative balances
- Now that we've fixed the root cause, we don't need them
- Keeps the transaction history clean

---

### Step 6: Final Verification
```bash
python check_actual_state.py
```

**Expected results:**
- ✅ All payment collections are IN
- ✅ All vault balances are positive
- ✅ No capital injections or security returns
- ✅ Only real transactions (payment collections, expenses, bank deposits, month closing)

---

### Step 7: Restart Application
```bash
sudo systemctl restart palmcash
```

---

### Step 8: Hard Refresh Browser
Tell all users to hard refresh:
- **Windows/Linux:** Ctrl + Shift + R
- **Mac:** Cmd + Shift + R

---

## ✅ Expected Final Balances:

After the complete fix:
- **KAMWALA SOUTH:** Positive balance from payment collections minus expenses
- **Chazanga:** K350 (K140 + K210 from payment collections)
- **KUKU:** Positive balance from payment collections minus expenses
- **MANDEVU:** Positive balance from payment collections

---

## 🔍 What Went Wrong:

1. Month closing reset vaults to K0.00 ✅
2. New transactions were made on June 1st ✅
3. Something caused payment collections to be recorded as OUT instead of IN ❌
4. This made vaults go negative ❌
5. Previous fix scripts added capital injections to compensate ⚠️

The fix scripts correct the direction and remove the compensating transactions.

---

## 📞 If Issues:

All scripts are safe to run multiple times. If something doesn't work:

1. Run `investigate_reversals.py` to check for REVERSAL transactions
2. Take screenshots of vault pages
3. Save output from `check_actual_state.py`
4. Contact developer with:
   - Screenshots
   - Script output
   - Description of what's still wrong

---

## 📚 Additional Resources:

- **VAULT_ISSUE_EXPLANATION.md** - Detailed explanation of the problem and solution
- **investigate_reversals.py** - Checks for manually reversed transactions
- **check_actual_state.py** - Shows current database state
- **fix_payment_collection_directions.py** - Main fix script
- **remove_capital_injections.py** - Cleanup script

---

**Created:** June 1, 2026  
**Last Updated:** June 1, 2026  
**Status:** Ready to execute  
**Priority:** URGENT
