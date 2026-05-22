# Fix Loan LV-000126 Application Date

## 🐛 Issue

Loan LV-000126 (Mercy Nakazwe) shows:
- **Applied**: May 22, 2026 (today)
- **Should be**: May 21, 2026 (yesterday - backdated)

The loan was created from a backdated application but the `application_date` field has `auto_now_add=True`, which always sets it to the current time.

---

## ✅ Fix Applied

### Code Fix (for future loans)
Updated `loans/views_application.py` to properly set backdated dates:
- Save loan first
- Then use `Loan.objects.filter(pk=loan.pk).update()` to set backdated dates
- This bypasses the `auto_now_add` constraint

### Management Command (for existing loan)
Created `fix_loan_lv000126_date.py` to fix the existing loan LV-000126

---

## 🚀 Deployment Steps

### Step 1: Pull Latest Code
```bash
ssh iwnd349@ipanel2
cd ~/www/palmcashloans.site
git pull origin main
```

**Expected Output**:
```
Updating b344c8f..3a0cd66
Fast-forward
 loans/views_application.py | 10 ++++---
 loans/management/commands/fix_loan_lv000126_date.py | 95 ++++++++++++++++++
 ...
```

### Step 2: Fix Existing Loan LV-000126
```bash
python manage.py fix_loan_lv000126_date
```

**Expected Output**:
```
============================================================
Fixing Loan LV-000126 Application Date
============================================================

✓ Found loan: LV-000126
  Borrower: Mercy Nakazwe
  Current application_date: 2026-05-22 ...
  Current approval_date: 2026-05-22 ...

✓ Found application: LA-A3B38172
  Application created_at: 2026-05-21 ...

============================================================
✅ SUCCESS
============================================================
Updated loan LV-000126:
  New application_date: 2026-05-21 ...
  New created_at: 2026-05-21 ...
  Approval date: 2026-05-22 ...
  Approval recorded at: 2026-05-22 ...
```

### Step 3: Restart Server
```bash
touch palmcash/wsgi.py
# OR
sudo systemctl restart palmcash
# OR
sudo supervisorctl restart palmcash
```

### Step 4: Verify Fix
1. Go to loan LV-000126 detail page
2. Check "Applied" date
3. Should now show: **May 21, 2026** (not May 22)

---

## 📊 What Gets Fixed

### Before Fix
```
Loan LV-000126:
  Applied: May 22, 2026  ❌ (wrong - shows today)
  Approved: May 22, 2026
  Disbursed: May 22, 2026
```

### After Fix
```
Loan LV-000126:
  Applied: May 21, 2026  ✅ (correct - backdated)
  Approved: May 22, 2026
  Disbursed: May 22, 2026
```

---

## 🎯 How It Works

### The Problem
The Loan model has:
```python
application_date = models.DateTimeField(auto_now_add=True)
```

This means Django automatically sets it to `timezone.now()` when the record is created, and you can't override it in the constructor.

### The Solution
1. Create the loan normally (gets today's date)
2. Immediately update it using `Loan.objects.filter(pk=loan.pk).update()`
3. The `update()` method bypasses field constraints like `auto_now_add`

### Code Change
```python
# Before (didn't work):
loan._state.adding = False
loan.created_at = loan_app.created_at
loan.save()

# After (works):
loan.save()
Loan.objects.filter(pk=loan.pk).update(
    application_date=loan_app.created_at,
    created_at=loan_app.created_at
)
```

---

## 🔄 Future Loans

All new loans created from backdated applications will automatically have the correct dates. No manual intervention needed.

---

## ✅ Verification Query

Check the loan dates in database:
```sql
SELECT 
    application_number,
    DATE(application_date) as applied_date,
    DATE(approval_date) as approved_date,
    DATE(disbursement_date) as disbursed_date,
    DATE(created_at) as created_date
FROM loans_loan
WHERE application_number = 'LV-000126';
```

**Expected Result**:
```
application_number | applied_date | approved_date | disbursed_date | created_date
LV-000126         | 2026-05-21   | 2026-05-22    | 2026-05-22     | 2026-05-21
```

---

## 📝 Summary

| Item | Status |
|------|--------|
| Code fix for future loans | ✅ Done |
| Management command created | ✅ Done |
| Pushed to GitHub | ✅ Done (commit 3a0cd66) |
| Ready for deployment | ✅ Yes |
| Estimated time | 5 minutes |

---

## 🎉 After Deployment

1. ✅ Loan LV-000126 will show correct backdated date (May 21)
2. ✅ All future backdated loans will work correctly
3. ✅ System timestamps still recorded for audit (approval_recorded_at, disbursement_recorded_at)

---

**Priority**: MEDIUM (cosmetic issue, doesn't affect functionality)  
**Impact**: Loan shows wrong application date  
**Fix Time**: 5 minutes  
**Risk**: Very Low (only updates date fields)

---

**Created**: May 22, 2026  
**Commit**: `3a0cd66`  
**Status**: ✅ Ready for Deployment
