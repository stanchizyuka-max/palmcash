# Vault Balance Issues - Fix Summary

## 🔍 Problems Found

### 1. **MANDEVU Branch - Negative Balance** ❌
- **Weekly Vault:** K-25.00 (NEGATIVE)
- **Cause:** Bank charges of K30 pushed vault negative after month closing
- **Fix:** Inject K25 capital

### 2. **Incorrect "Balance After" Values** ❌
- All branches showing incorrect sequential balances in transaction history
- **Examples:**
  - Expenses making balance go UP instead of DOWN
  - Capital Injection + Security Return both showing K0.00 balance
  - Sequential transactions not calculating cumulative balance correctly

### 3. **Other Branches - Positive Balances** ✅
- **KUKU:** K7,800 (legitimate transactions after month closing)
- **KAMWALA SOUTH:** K1,730 (legitimate transactions after month closing)
- **CHAZANGA:** K350 (legitimate transactions after month closing)
- These are OKAY - normal business operations

---

## 🔧 Solutions Created

### **Script 1: fix_mandevu_negative_balance.py**
**Purpose:** Fix MANDEVU's negative K25 balance

**What it does:**
- Checks MANDEVU weekly vault balance
- If negative, injects capital to bring it to K0.00
- Creates capital_injection transaction
- Updates vault model

**Run on server:**
```bash
python fix_mandevu_negative_balance.py
```

---

### **Script 2: recalculate_all_balance_after_values.py**
**Purpose:** Fix all incorrect "balance_after" values in transaction history

**What it does:**
- Processes ALL vault transactions in chronological order
- Recalculates balance_after for each transaction
- Tracks separate balances for daily and weekly vaults
- Updates vault model balances to match final calculated values
- Shows which transactions were updated

**Run on server:**
```bash
python recalculate_all_balance_after_values.py
```

**Safety:**
- Only updates the `balance_after` field
- Does NOT change transaction amounts
- Does NOT create or delete transactions
- Safe to run multiple times

---

### **Script 3: investigate_capital_and_security_transactions.py**
**Purpose:** Show where capital injection and security return transactions came from

**What it does:**
- Lists all capital injection transactions
- Lists all security return transactions
- Shows which script created each transaction
- Explains why they were created
- Calculates current security balances

**Run on server:**
```bash
python investigate_capital_and_security_transactions.py
```

---

## 📋 Execution Order

Run these scripts in order on the production server:

```bash
# 1. Fix MANDEVU negative balance
python fix_mandevu_negative_balance.py

# 2. Recalculate all balance_after values
python recalculate_all_balance_after_values.py

# 3. (Optional) Investigate capital/security transactions
python investigate_capital_and_security_transactions.py

# 4. Restart application
sudo systemctl restart palmcash
```

Then all users must **hard refresh** their browsers:
- **Windows/Linux:** Ctrl + Shift + R
- **Mac:** Cmd + Shift + R

---

## ✅ Expected Results

After running all scripts:

### **MANDEVU:**
- Weekly Vault: K0.00 (fixed from -K25)
- All balance_after values correct

### **All Branches:**
- Balance After column shows correct sequential values
- Each IN transaction increases balance
- Each OUT transaction decreases balance
- Final balance matches vault balance at top of page

### **Transaction History:**
- Reading from oldest to newest, balances flow correctly
- No jumps or incorrect calculations
- Vault model balances match last transaction

---

## 🔍 Root Cause Analysis

**Why did this happen?**

The `balance_after` field is calculated when transactions are created. However:

1. **Multiple code paths create transactions:**
   - `vault_services.py` (correct way)
   - `dashboard/vault_views.py` (direct creation)
   - `expenses/views.py` (direct creation)
   - `payments/views.py` (direct creation)
   - `clients/views.py` (direct creation)

2. **Timing issues:**
   - If vault balance isn't updated before creating transaction
   - If multiple transactions happen simultaneously
   - If balance is calculated incorrectly

3. **Month closing complexity:**
   - Multiple transactions created in sequence
   - Security returns, capital injections, month closings
   - Each affects the balance differently

**The Fix:**
- Recalculate all balance_after values in strict chronological order
- Ensure vault model balances match the calculated values
- This creates a clean, correct transaction history

---

## 📞 Support

If issues persist after running scripts:
1. Check the script output for errors
2. Verify users have hard refreshed browsers
3. Check vault page transaction list
4. Run `investigate_capital_and_security_transactions.py` for details

---

**Created:** June 1, 2026  
**Status:** Ready to execute on production server
