# 🚀 Simple Deployment Guide - Backdating Fix

## Quick 5-Step Deployment

### Step 1: Pull Latest Code
```bash
cd ~/www/palmcashloans.site
git pull origin main
```

### Step 2: Add Database Columns
```bash
python manage.py add_audit_columns
```

**Expected Output:**
```
============================================================
Adding Audit Timestamp Columns
============================================================

🔍 Checking if columns already exist...
📝 No columns exist yet, will add both

Adding approval_recorded_at column...
  ✅ approval_recorded_at added
Adding disbursement_recorded_at column...
  ✅ disbursement_recorded_at added

============================================================
✅ Columns Added Successfully
============================================================

📋 Column Details:

  Column: approval_recorded_at
    Type: datetime(6)
    Nullable: YES
    Default: NULL
    Comment: System timestamp: when approval was recorded in the system

  Column: disbursement_recorded_at
    Type: datetime(6)
    Nullable: YES
    Default: NULL
    Comment: System timestamp: when disbursement was recorded in the system

🎉 Done! You can now run:
   python manage.py fix_backdated_loans --dry-run
```

### Step 3: Preview Changes (Dry Run)
```bash
python manage.py fix_backdated_loans --dry-run
```

**Review the output** - it will show you what will be changed without actually changing anything.

### Step 4: Fix Existing Loans
```bash
python manage.py fix_backdated_loans
```

**Expected Output:**
```
⚠️  LIVE MODE - Changes will be saved to database

📋 Found 101 approved loan applications

🔧 Fixing Loan LV-000123
   Borrower: John Doe
   Application Date: 2026-01-15
   Current Loan Created: 2026-05-22
   Difference: 127 days
   New Disbursement Date: 2026-01-16
   Regenerating payment schedule...
   Payment schedule: 30 → 30 schedules
   ✅ Fixed successfully

[... more loans ...]

============================================================
📊 SUMMARY
============================================================
Total Applications Checked: 101
✅ Loans Fixed: 85
⏭️  Loans Skipped (already aligned): 16
❌ Errors: 0

✅ All changes have been saved to the database.
```

### Step 5: Restart Server
```bash
sudo systemctl restart gunicorn
```

**Verify it's running:**
```bash
sudo systemctl status gunicorn
```

---

## ✅ That's It!

Your system now has:
- ✅ Audit timestamp columns added
- ✅ All backdated loans fixed
- ✅ Consistent dates across all loans
- ✅ Proper payment schedules

---

## 🔍 Verify Everything Works

### Check a Loan:
```bash
python manage.py shell
```

```python
from loans.models import Loan

# Get any loan
loan = Loan.objects.first()

print(f"Loan: {loan.application_number}")
print(f"Created: {loan.created_at}")
print(f"Approval: {loan.approval_date}")
print(f"Approval Recorded: {loan.approval_recorded_at}")
print(f"Disbursement: {loan.disbursement_date}")
print(f"Disbursement Recorded: {loan.disbursement_recorded_at}")

exit()
```

### Check Website:
- Visit https://palmcashloans.site
- Login and check a few loans
- Verify dates look correct

---

## 🆘 Troubleshooting

### If Step 2 Fails:
```bash
# Check database connection
python manage.py dbshell
# Type: exit

# Try again
python manage.py add_audit_columns
```

### If Step 4 Shows Errors:
- Most errors are non-fatal
- Script continues with other loans
- Can re-run to fix any that failed

### If Server Won't Start:
```bash
# Check logs
sudo journalctl -u gunicorn -n 50

# Check for errors
python manage.py check

# Restart again
sudo systemctl restart gunicorn
```

---

## 📞 Need Help?

If you see errors:
1. Copy the error message
2. Check which step failed
3. Try running that step again

The scripts are safe to run multiple times!

---

**Created**: May 22, 2026  
**Commit**: a44780e  
**Status**: ✅ Ready to Deploy
