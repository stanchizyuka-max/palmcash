# Duplicate Expenses Checker & Remover

## 🎯 Purpose

Check for and safely remove duplicate expenses in MANDEVU BRANCH (or any branch).

---

## 📋 Two Scripts Provided

### 1. `check_duplicate_expenses.py` - DIAGNOSTIC ONLY
**Purpose**: Identify duplicate expenses without making any changes

**What it checks:**
- ✅ Exact duplicates (same date, amount, description)
- ✅ Near duplicates (same date/amount, within 1 hour)
- ✅ Grouped duplicates (multiple expenses with same date/amount)
- ✅ Description duplicates (same description on same day)
- ✅ All branches summary

**Safe to run**: YES - Read-only, makes no changes

### 2. `remove_duplicate_expenses.py` - DELETION TOOL
**Purpose**: Safely remove duplicate expenses after review

**What it does:**
- ⚠️ Deletes duplicate expense records
- ⚠️ Reverses vault transactions
- ⚠️ Returns money to vault
- ⚠️ Requires confirmation at each step

**Safe to run**: ONLY after backup and review

---

## 🚀 Step-by-Step Process

### Step 1: Check for Duplicates (SAFE)

```bash
cd ~/www/palmcashloans.site
python check_duplicate_expenses.py
```

**What you'll see:**
```
============================================================
DUPLICATE EXPENSES CHECKER
============================================================

🔍 Checking for duplicate expenses in: MANDEVU BRANCH
--------------------------------------------------------------------

📊 Total expenses in MANDEVU BRANCH: 59

============================================================
STRATEGY 1: Exact Duplicates (Same Amount, Date, Description)
============================================================

⚠️  Found 3 exact duplicate(s):

Duplicate Set #1:
  Original ID: 45
    Date: 2026-05-06
    Amount: K100.00
    Description: Transport to bank
    Category: Fuel
    Recorded by: Manager Name
    Recorded at: 2026-05-06 10:30:00

  Duplicate ID: 46
    Date: 2026-05-06
    Amount: K100.00
    Description: Transport to bank
    Category: Fuel
    Recorded by: Manager Name
    Recorded at: 2026-05-06 10:31:00
  Time difference: 1.0 minutes
--------------------------------------------------------------------
```

**Review the output carefully!**

### Step 2: Backup Database (REQUIRED)

```bash
# Create backup before any deletion
mysqldump -u your_username -p palmcash_db > backup_before_cleanup_$(date +%Y%m%d).sql

# Or if using PostgreSQL
pg_dump palmcash_db > backup_before_cleanup_$(date +%Y%m%d).sql
```

**Verify backup was created:**
```bash
ls -lh backup_before_cleanup_*.sql
```

### Step 3: Remove Duplicates (CAREFUL)

```bash
python remove_duplicate_expenses.py
```

**You'll be asked:**
```
⚠️  WARNING: This script will DELETE duplicate expenses!
⚠️  Make sure you have reviewed the duplicates first!
⚠️  Run check_duplicate_expenses.py first to identify duplicates!

Have you run check_duplicate_expenses.py and reviewed the results? (yes/no):
```

Type `yes` and press Enter

```
Do you have a database backup? (yes/no):
```

Type `yes` and press Enter

**Review the duplicates to be deleted:**
```
⚠️  Found 3 duplicate expense(s) to remove:

Duplicate #1:
  KEEPING: ID 45 - 2026-05-06 - K100.00 - Transport to bank
           Recorded at: 2026-05-06 10:30:00
  DELETING: ID 46 - 2026-05-06 - K100.00 - Transport to bank
            Recorded at: 2026-05-06 10:31:00
```

**Final confirmation:**
```
Proceed with deletion? Type 'DELETE' to confirm:
```

Type `DELETE` (all caps) and press Enter

### Step 4: Verify Results

```bash
# Run checker again to verify no duplicates remain
python check_duplicate_expenses.py
```

Should show:
```
✅ No exact duplicates found
```

---

## 🔍 Understanding the Duplicate Detection

### Strategy 1: Exact Duplicates
**Criteria**: Same date, amount, description, and category

**Example:**
```
Expense 1: 2026-05-06 | K100 | "Transport to bank" | Fuel
Expense 2: 2026-05-06 | K100 | "Transport to bank" | Fuel
Result: EXACT DUPLICATE ⚠️
```

### Strategy 2: Near Duplicates
**Criteria**: Same date and amount, recorded within 1 hour

**Example:**
```
Expense 1: 2026-05-06 | K100 | Recorded at 10:30
Expense 2: 2026-05-06 | K100 | Recorded at 10:35
Time difference: 5 minutes
Result: NEAR DUPLICATE ⚠️
```

### Strategy 3: Grouped Duplicates
**Criteria**: Multiple expenses with same date and amount

**Example:**
```
Group: 2026-05-06 | K100 (3 expenses)
  - ID 45: "Transport"
  - ID 46: "Transport to bank"
  - ID 47: "Fuel for transport"
Result: GROUPED DUPLICATES ⚠️
```

### Strategy 4: Description Duplicates
**Criteria**: Same description on same day

**Example:**
```
Date: 2026-05-06 | Description: "Transport to bank"
  - ID 45: K100
  - ID 46: K100
  - ID 47: K50
Result: DESCRIPTION DUPLICATES ⚠️
```

---

## ⚠️ Important Safety Features

### 1. Keeps the First Record
The script always keeps the **first recorded** expense and deletes later duplicates.

### 2. Reverses Vault Transactions
When deleting an expense, the script:
- Finds the related vault transaction
- Creates a reversal transaction
- Returns money to the vault
- Maintains audit trail

### 3. Transaction Safety
Uses Django's `transaction.atomic()` - if any error occurs, ALL changes are rolled back.

### 4. Multiple Confirmations
Requires:
- Confirmation that you ran the checker
- Confirmation that you have a backup
- Final confirmation with 'DELETE' keyword

---

## 📊 What Gets Deleted vs Kept

### Scenario: Two Identical Expenses

```
Expense A:
  ID: 45
  Date: 2026-05-06
  Amount: K100
  Description: "Transport"
  Recorded at: 10:30:00
  
Expense B:
  ID: 46
  Date: 2026-05-06
  Amount: K100
  Description: "Transport"
  Recorded at: 10:31:00
```

**Result:**
- ✅ **KEEP**: Expense A (ID 45) - First recorded
- ❌ **DELETE**: Expense B (ID 46) - Duplicate

**Vault Impact:**
- Expense A's vault transaction: Kept
- Expense B's vault transaction: Reversed (money returned to vault)

---

## 🔧 Manual Review Option

If you want to manually review before using the script:

```python
python manage.py shell

from expenses.models import Expense

# Get MANDEVU BRANCH expenses
expenses = Expense.objects.filter(branch="MANDEVU BRANCH").order_by('expense_date', 'amount')

# Check for duplicates manually
for exp in expenses:
    print(f"ID: {exp.id} | {exp.expense_date} | K{exp.amount} | {exp.description}")
```

---

## 🆘 Troubleshooting

### Problem: Script says "No duplicates found" but you see them

**Possible causes:**
1. Descriptions have slight differences (extra spaces, capitalization)
2. Amounts are slightly different (K100.00 vs K100.01)
3. Dates are different (check time component)

**Solution**: Review the grouped duplicates section - it's more lenient

### Problem: Script deleted wrong expense

**Solution**: Restore from backup
```bash
mysql -u username -p palmcash_db < backup_before_cleanup_20260507.sql
```

### Problem: Vault balance is wrong after deletion

**Solution**: The script should have reversed transactions. Check:
```bash
python check_vault_transactions.py
```

---

## 📝 Example Output

### Before Cleanup:
```
MANDEVU BRANCH: 59 expenses, 3 exact duplicates
```

### After Cleanup:
```
✅ Successfully deleted: 3 expense(s)
✅ Vault transactions reversed: 3
📊 Remaining expenses in MANDEVU BRANCH: 56

MANDEVU BRANCH: 56 expenses, 0 exact duplicates
```

---

## ✅ Checklist

Before running removal script:

- [ ] Run `check_duplicate_expenses.py` to identify duplicates
- [ ] Review the duplicate list carefully
- [ ] Create database backup
- [ ] Verify backup file exists and has size > 0
- [ ] Understand which expenses will be kept vs deleted
- [ ] Have a plan to restore if something goes wrong
- [ ] Run during low-traffic time (not during business hours)

After running removal script:

- [ ] Run `check_duplicate_expenses.py` again to verify
- [ ] Check vault balances are correct
- [ ] Review expense list in dashboard
- [ ] Verify reports show correct totals
- [ ] Keep backup for at least 30 days

---

## 🎯 Summary

**Two scripts:**
1. `check_duplicate_expenses.py` - Safe diagnostic tool
2. `remove_duplicate_expenses.py` - Deletion tool (requires backup)

**Process:**
1. Check → 2. Backup → 3. Remove → 4. Verify

**Safety:**
- Multiple confirmations required
- Keeps first record, deletes duplicates
- Reverses vault transactions
- Transaction rollback on error
- Maintains audit trail

**Always backup before deletion!** 🔒
