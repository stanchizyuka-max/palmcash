# 🔧 Dual-Vault System - Required Code Updates

## Overview
This document lists ALL files that need to be updated to support the dual-vault system.

---

## 📋 FILES TO UPDATE

### **1. Core Vault Services**
- [ ] `loans/vault_services.py` - Update all vault operations
- [ ] `dashboard/vault_views.py` - Update vault management views

### **2. Loan Operations**
- [ ] `loans/views.py` - Update disbursement logic
- [ ] `loans/views_application.py` - Update approval flow
- [ ] `loans/utils.py` - Update helper functions

### **3. Payment Operations**
- [ ] `payments/views.py` - Update collection recording
- [ ] `payments/models.py` - Update payment processing

### **4. Dashboard Views**
- [ ] `dashboard/views.py` - Update all dashboard displays
- [ ] `dashboard/vault_views.py` - Update vault displays

### **5. Templates - Manager Dashboard**
- [ ] `dashboard/templates/dashboard/manager_enhanced.html`
- [ ] `dashboard/templates/dashboard/vault.html`
- [ ] `dashboard/templates/dashboard/vault_month_close.html`
- [ ] `dashboard/templates/dashboard/vault_month_history.html`

### **6. Templates - Admin Dashboard**
- [ ] `dashboard/templates/dashboard/admin_dashboard.html`

### **7. Templates - Officer Dashboard**
- [ ] `dashboard/templates/dashboard/loan_officer_enhanced.html`

### **8. Templates - Vault Operations**
- [ ] `templates/expenses/vault_transaction_form.html`
- [ ] `templates/expenses/vault_transaction_list.html`

### **9. Reports**
- [ ] `reports/views.py` - Update financial reports
- [ ] `reports/templates/` - Update report templates

### **10. Expenses**
- [ ] `expenses/views.py` - Update expense recording
- [ ] `expenses/forms.py` - Update vault transaction forms

---

## 🎯 CRITICAL CHANGES NEEDED

### **1. Vault Balance Retrieval**

**Current Code:**
```python
vault = branch.vault
balance = vault.balance
```

**New Code:**
```python
daily_vault = branch.daily_vault
weekly_vault = branch.weekly_vault
daily_balance = daily_vault.balance
weekly_balance = weekly_vault.balance
total_balance = daily_balance + weekly_balance
```

### **2. Loan Disbursement**

**Current Code:**
```python
def disburse_loan(loan):
    vault = loan.loan_officer.branch.vault
    vault.balance -= loan.principal_amount
    vault.save()
```

**New Code:**
```python
def disburse_loan(loan):
    # Automatically select correct vault
    if loan.repayment_frequency == 'daily':
        vault = loan.loan_officer.branch.daily_vault
    else:
        vault = loan.loan_officer.branch.weekly_vault
    
    vault.balance -= loan.principal_amount
    vault.save()
```

### **3. Payment Collection**

**Current Code:**
```python
def record_payment(payment):
    vault = payment.loan.loan_officer.branch.vault
    vault.balance += payment.amount
    vault.save()
```

**New Code:**
```python
def record_payment(payment):
    # Route to correct vault based on loan type
    if payment.loan.repayment_frequency == 'daily':
        vault = payment.loan.loan_officer.branch.daily_vault
    else:
        vault = payment.loan.loan_officer.branch.weekly_vault
    
    vault.balance += payment.amount
    vault.save()
```

### **4. Vault Transaction Recording**

**Current Code:**
```python
VaultTransaction.objects.create(
    branch=branch.name,
    amount=amount,
    transaction_type='loan_disbursement',
    ...
)
```

**New Code:**
```python
VaultTransaction.objects.create(
    branch=branch.name,
    vault_type=loan.repayment_frequency,  # NEW: Required field
    amount=amount,
    transaction_type='loan_disbursement',
    ...
)
```

### **5. Dashboard Template**

**Current Template:**
```html
<div class="vault-balance">
    <h3>Vault Balance</h3>
    <p>K{{ vault.balance|floatformat:2 }}</p>
</div>
```

**New Template:**
```html
<div class="vault-balances">
    <div class="daily-vault">
        <h3>Daily Vault</h3>
        <p>K{{ daily_vault.balance|floatformat:2 }}</p>
    </div>
    <div class="weekly-vault">
        <h3>Weekly Vault</h3>
        <p>K{{ weekly_vault.balance|floatformat:2 }}</p>
    </div>
    <div class="total">
        <h3>Total</h3>
        <p>K{{ total_balance|floatformat:2 }}</p>
    </div>
</div>
```

### **6. Bank Deposit Form**

**Current Form:**
```html
<form method="post">
    <input type="number" name="amount" required>
    <input type="text" name="reference">
    <button type="submit">Deposit</button>
</form>
```

**New Form:**
```html
<form method="post">
    <input type="number" name="amount" required>
    <input type="text" name="reference">
    
    <!-- NEW: Vault selection -->
    <label>Deposit to:</label>
    <select name="vault_type" required>
        <option value="daily">Daily Vault</option>
        <option value="weekly">Weekly Vault</option>
    </select>
    
    <button type="submit">Deposit</button>
</form>
```

---

## 🔍 SEARCH & REPLACE PATTERNS

### **Pattern 1: Vault Access**
**Find:** `branch.vault`
**Replace with:** `branch.daily_vault` or `branch.weekly_vault` (context-dependent)

### **Pattern 2: Vault Balance**
**Find:** `vault.balance`
**Replace with:** Check if we need daily, weekly, or both

### **Pattern 3: VaultTransaction Creation**
**Find:** `VaultTransaction.objects.create(`
**Add:** `vault_type=...` parameter

---

## 📊 ESTIMATED CHANGES

- **Views:** ~15 files
- **Templates:** ~20 files
- **Models:** ~3 files
- **Forms:** ~5 files
- **Utils:** ~3 files

**Total:** ~46 files need updates

---

## ⚠️ BREAKING CHANGES

These operations will BREAK until updated:

1. ❌ Loan disbursement
2. ❌ Payment collection
3. ❌ Bank deposits/withdrawals
4. ❌ Vault balance display
5. ❌ Month closing
6. ❌ Reports generation
7. ❌ Capital injection
8. ❌ Branch transfers

---

## 🎯 RECOMMENDED APPROACH

### **Option A: Big Bang (Risky)**
- Update all files at once
- Deploy during maintenance window
- High risk, fast completion

### **Option B: Phased (Safer)**
- Phase 1: Database (✅ Done)
- Phase 2: Core operations (disbursement, collection)
- Phase 3: Bank operations
- Phase 4: Reports and UI
- Phase 5: Cleanup

### **Option C: Parallel (Safest)**
- Keep old vault working
- Add dual-vault support alongside
- Gradually migrate features
- Remove old code after validation

---

## 🚨 CRITICAL: System Will Break!

**After running the migration, the system WILL NOT WORK until we update the code!**

Why?
- Code still references `branch.vault` (doesn't exist anymore)
- VaultTransaction requires `vault_type` (not provided)
- Templates expect single vault (now have two)

**Solution:** We must update ALL code before deploying to production.

---

## ✅ TESTING CHECKLIST

After updating code, test:

- [ ] Disburse daily loan
- [ ] Disburse weekly loan
- [ ] Collect daily payment
- [ ] Collect weekly payment
- [ ] Bank deposit to daily vault
- [ ] Bank deposit to weekly vault
- [ ] Bank withdrawal from daily vault
- [ ] Bank withdrawal from weekly vault
- [ ] View manager dashboard
- [ ] View officer dashboard
- [ ] View admin dashboard
- [ ] Generate vault report
- [ ] Close month for both vaults
- [ ] Transfer between vaults (if allowed)

---

## 📅 IMPLEMENTATION TIMELINE

**Recommended:**
1. **Week 1:** Update core operations (disbursement, collection)
2. **Week 2:** Update bank operations and forms
3. **Week 3:** Update dashboards and reports
4. **Week 4:** Testing and validation
5. **Week 5:** Deploy to production

**Fast Track (Risky):**
1. **Day 1-2:** Update all code
2. **Day 3:** Test on staging
3. **Day 4:** Deploy to production
4. **Day 5:** Monitor and fix issues

---

## 🎓 NEXT STEPS

1. **Decide approach:** Big Bang vs Phased vs Parallel
2. **Create backup:** Full database backup
3. **Update code:** Start with core operations
4. **Test thoroughly:** On staging environment
5. **Deploy:** During maintenance window
6. **Monitor:** Watch for errors

---

**IMPORTANT:** Do NOT run the migration on production until we've updated the code!

The migration creates the database structure, but the application code still needs to be updated to use it.
