# Expense Category Duplicate Fix & Data Bundle Addition

**Date**: May 2, 2026  
**Status**: ✅ Code changes committed and pushed  
**Action Required**: Run scripts on server

---

## Problem Summary

### Issue 1: Duplicate "Other" Entries
- User reported seeing 3 "Other" entries in the expense category dropdown
- Duplicates existed in both `ExpenseCode` and `ExpenseCategory` tables
- Caused confusion when creating expenses

### Issue 2: Missing "Data Bundle" Category
- User requested adding "Data Bundle" as a new expense category
- Needed for tracking mobile data and internet expenses

### Issue 3: Hardcoded "Other" Option
- Expense form had a hardcoded `<option value="other">Other</option>`
- View had special logic to create "Other" entry if it didn't exist
- This could create additional duplicates

---

## Solution Implemented

### 1. Code Changes (✅ Completed)

#### A. Updated `dashboard/templates/dashboard/expense_form.html`
**Changes:**
- Removed hardcoded `<option value="other">Other</option>` from dropdown
- All options now come from database only
- Updated info box to be more generic (removed hardcoded category list)

**Before:**
```html
<option value="">-- Select Category --</option>
{% for code in expense_codes %}
<option value="{{ code.id }}">{{ code.name }}</option>
{% endfor %}
<option value="other">Other</option>  <!-- REMOVED -->
```

**After:**
```html
<option value="">-- Select Category --</option>
{% for code in expense_codes %}
<option value="{{ code.id }}">{{ code.name }}</option>
{% endfor %}
```

#### B. Updated `dashboard/views.py` (expense_create function)
**Changes:**
- Removed special handling for `expense_code_id == 'other'`
- Simplified to always get expense code from database by ID

**Before:**
```python
if expense_code_id == 'other':
    expense_code, _ = ExpenseCode.objects.get_or_create(
        code='OTHER',
        defaults={'name': 'Other', 'description': 'Other expenses', 'is_active': True}
    )
else:
    expense_code = ExpenseCode.objects.get(id=expense_code_id)
```

**After:**
```python
# Get expense code
expense_code = ExpenseCode.objects.get(id=expense_code_id)
```

### 2. Database Cleanup Scripts (⏳ Pending Execution)

#### A. `remove_duplicate_other.py`
**Purpose:** Remove duplicate "Other" entries from both tables

**What it does:**
1. Finds all "Other" entries in `ExpenseCategory` table
2. Keeps the first one (lowest ID)
3. Updates any expenses using duplicates to point to the kept entry
4. Deletes duplicate entries
5. Repeats for `ExpenseCode` table
6. Shows detailed before/after summary

**Safety features:**
- Safe to run multiple times
- Preserves all expense records
- Updates foreign key references before deletion
- No data loss

#### B. `add_data_bundle_category.py`
**Purpose:** Add "Data Bundle" expense category

**What it does:**
1. Checks if "Data Bundle" already exists
2. Creates it if missing
3. Shows all active categories

**Safety features:**
- Safe to run multiple times
- Won't create duplicates
- Shows confirmation message

---

## Execution Instructions

### Step 1: Run Cleanup Script
```bash
cd ~/www/palmcashloans.site
python remove_duplicate_other.py
```

**Expected output:**
```
======================================================================
REMOVING DUPLICATE 'OTHER' ENTRIES
======================================================================

1. Checking ExpenseCategory for duplicates...
----------------------------------------------------------------------
Found X 'Other' categories

Keeping: ID X - Other
Removing X duplicate(s):
  - ID X: Updating X expense(s) to use ID X
    ✓ Deleted duplicate ID X

✓ Removed X duplicate ExpenseCategory entries

2. Checking ExpenseCode for duplicates...
----------------------------------------------------------------------
Found X 'Other' expense codes

Keeping: ID X - CODE - Other
Removing X duplicate(s):
  - ID X (CODE): Updating X expense(s) to use ID X
    ✓ Deleted duplicate ID X

✓ Removed X duplicate ExpenseCode entries

======================================================================
FINAL STATE
======================================================================
[Shows all categories and codes with usage counts]

======================================================================
✓ CLEANUP COMPLETE
======================================================================
```

### Step 2: Add Data Bundle Category
```bash
python add_data_bundle_category.py
```

**Expected output:**
```
✓ Created 'Data Bundle' category (ID: X)

All Expense Categories:
============================================================
  - Cleaning costs
  - Data Bundle          ← NEW
  - Other                ← Only ONE entry now
  - Rentals
  - Stationery
  - Talk time
  - Transport

Total: 7 active categories
```

### Step 3: Restart Server
```bash
sudo systemctl restart gunicorn
```

### Step 4: Verify Changes
1. Go to: https://palmcashloans.site/dashboard/expenses/create/?branch=Kamwala%20south
2. Check "Expense Category" dropdown
3. Verify:
   - ✅ "Data Bundle" appears in the list
   - ✅ Only ONE "Other" entry exists
   - ✅ No duplicate entries

---

## Technical Details

### Database Models Affected

#### ExpenseCode Model
```python
class ExpenseCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
```

#### ExpenseCategory Model
```python
class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
```

#### Expense Model (Foreign Keys)
```python
class Expense(models.Model):
    expense_code = models.ForeignKey(ExpenseCode, ...)
    category = models.ForeignKey(ExpenseCategory, ...)
    # ... other fields
```

### Why Duplicates Occurred
1. **Hardcoded option**: Form had `<option value="other">Other</option>`
2. **get_or_create logic**: View used `get_or_create` which could create duplicates if code field differed
3. **Manual entries**: Possible manual database entries or migrations

### How Fix Prevents Future Duplicates
1. **No hardcoded options**: All categories come from database
2. **No special handling**: View treats all categories equally
3. **Database constraints**: `unique=True` on name/code fields prevents duplicates
4. **Single source of truth**: Database is the only source for categories

---

## Files Changed

### Modified Files
1. `dashboard/templates/dashboard/expense_form.html`
   - Removed hardcoded "Other" option
   - Updated info box text

2. `dashboard/views.py`
   - Simplified expense_create function
   - Removed special "other" handling

### New Files
1. `remove_duplicate_other.py` - Cleanup script
2. `add_data_bundle_category.py` - Add new category script
3. `RUN_THESE_SCRIPTS.md` - Execution instructions
4. `EXPENSE_CATEGORY_FIX.md` - This documentation

---

## Git History

**Commit**: `d68f428`  
**Message**: Fix expense category duplicates and add Data Bundle category  
**Branch**: main  
**Status**: ✅ Pushed to remote

---

## Rollback Plan (If Needed)

If something goes wrong:

1. **Restore from backup** (scripts create backups before deletion)
2. **Revert git commit**:
   ```bash
   git revert d68f428
   git push origin main
   sudo systemctl restart gunicorn
   ```

3. **Manual database fix**:
   ```python
   # In Django shell
   from expenses.models import ExpenseCode, ExpenseCategory
   
   # Check current state
   print(ExpenseCode.objects.filter(name__iexact='other').count())
   print(ExpenseCategory.objects.filter(name__iexact='other').count())
   ```

---

## Testing Checklist

After running scripts:

- [ ] Run `remove_duplicate_other.py` successfully
- [ ] Run `add_data_bundle_category.py` successfully
- [ ] Restart gunicorn server
- [ ] Open expense creation form
- [ ] Verify "Data Bundle" appears in dropdown
- [ ] Verify only ONE "Other" entry exists
- [ ] Create a test expense with "Data Bundle" category
- [ ] Verify expense saves correctly
- [ ] Check vault transaction is created
- [ ] Verify expense appears in expense list

---

## Related Issues

- **Task 7**: Add Data Bundle expense category ✅
- **Task 7**: Remove duplicate "Other" entries ✅

---

## Notes

- Scripts are idempotent (safe to run multiple times)
- No existing expense data will be lost
- All foreign key references are preserved
- Changes are backward compatible

---

**Next Steps:**
1. ⏳ User needs to run `remove_duplicate_other.py` on server
2. ⏳ User needs to run `add_data_bundle_category.py` on server
3. ⏳ User needs to restart gunicorn
4. ⏳ User needs to verify changes in browser

