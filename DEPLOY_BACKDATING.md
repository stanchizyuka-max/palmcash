# 🚀 Quick Deployment Guide - Full Backdating

## ⚠️ IMPORTANT: Read Before Deploying

This update implements full backdating for loans. It will:
- ✅ Fix existing backdated loans to have consistent dates
- ✅ Regenerate payment schedules based on backdated dates
- ✅ Add audit trail fields to track system timestamps

**Estimated Time**: 10-15 minutes  
**Downtime Required**: ~2 minutes (during restart)

---

## 📋 Pre-Deployment Checklist

- [ ] Backup database
- [ ] Notify users of brief maintenance
- [ ] Have database backup ready to restore if needed

---

## 🔧 Deployment Steps

### 1. Backup Database (CRITICAL!)
```bash
cd /var/www/iwnd349/data/www/palmcashloans.site
python manage.py dumpdata > backup_before_backdating_$(date +%Y%m%d_%H%M%S).json
```

**Verify backup was created:**
```bash
ls -lh backup_before_backdating_*.json
```

### 2. Pull Latest Code
```bash
git pull origin main
```

**Expected output:**
```
Updating 4d39bbc..c4026f6
Fast-forward
 BACKDATED_LOAN_WORKFLOW.md                        | 450 +++++++++++++++++++++
 FULL_BACKDATING_IMPLEMENTATION.md                 | 547 +++++++++++++++++++++++++
 loans/management/commands/fix_backdated_loans.py  | 250 +++++++++++
 loans/migrations/0999_add_audit_timestamps.py     |  23 +
 loans/models.py                                   |  14 +
 loans/views.py                                    |  25 +-
 loans/views_application.py                        |   8 +-
 7 files changed, 997 insertions(+), 3 deletions(-)
```

### 3. Run Migration
```bash
python manage.py migrate loans
```

**Expected output:**
```
Running migrations:
  Applying loans.0999_add_audit_timestamps... OK
```

### 4. Preview Changes (Dry Run)
```bash
python manage.py fix_backdated_loans --dry-run --verbose
```

**Review the output carefully!**
- Check how many loans will be fixed
- Verify the date changes look correct
- Note any errors or warnings

### 5. Fix Existing Loans
```bash
python manage.py fix_backdated_loans
```

**Expected output:**
```
⚠️  LIVE MODE - Changes will be saved to database

📋 Found X approved loan applications

🔧 Fixing Loan LV-XXXXXX
   Borrower: John Doe
   Application Date: 2026-01-15
   Current Loan Created: 2026-05-22
   Difference: 127 days
   New Disbursement Date: 2026-01-16
   Regenerating payment schedule...
   Payment schedule: 30 → 30 schedules
   ✅ Fixed successfully

============================================================
📊 SUMMARY
============================================================
Total Applications Checked: X
✅ Loans Fixed: X
⏭️  Loans Skipped (already aligned): X
❌ Errors: 0

✅ All changes have been saved to the database.
```

### 6. Clear Python Cache
```bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

### 7. Restart Server
```bash
sudo systemctl restart gunicorn
```

### 8. Verify Server is Running
```bash
sudo systemctl status gunicorn
```

**Expected output:**
```
● gunicorn.service - gunicorn daemon
   Active: active (running) since ...
```

---

## ✅ Post-Deployment Verification

### 1. Check a Backdated Loan
```bash
python manage.py shell
```

```python
from loans.models import Loan, LoanApplication
from datetime import date

# Find a backdated application
app = LoanApplication.objects.filter(
    created_at__date__lt=date(2026, 5, 1)
).first()

if app:
    print(f"Application: {app.application_number}")
    print(f"Application Date: {app.created_at}")
    
    # Find its loan
    loan = Loan.objects.filter(
        borrower=app.borrower,
        principal_amount=app.loan_amount
    ).first()
    
    if loan:
        print(f"\nLoan: {loan.application_number}")
        print(f"Loan Created: {loan.created_at}")
        print(f"Approval Date: {loan.approval_date}")
        print(f"Approval Recorded: {loan.approval_recorded_at}")
        print(f"Disbursement Date: {loan.disbursement_date}")
        print(f"Disbursement Recorded: {loan.disbursement_recorded_at}")
        
        # Check if dates match
        if loan.created_at.date() == app.created_at.date():
            print("\n✅ Dates are aligned!")
        else:
            print("\n❌ Dates are NOT aligned!")
    else:
        print("No loan found for this application")
else:
    print("No backdated applications found")

exit()
```

### 2. Check Website
- Visit https://palmcashloans.site
- Login as admin
- Check a few loan details
- Verify dates look correct

### 3. Check Reports
- Go to Reports → Loan Reports
- Verify historical data looks correct
- Check vault reports for processing fees

---

## 🔄 Rollback (If Needed)

If something goes wrong:

### 1. Stop Server
```bash
sudo systemctl stop gunicorn
```

### 2. Restore Database
```bash
python manage.py flush --no-input
python manage.py loaddata backup_before_backdating_YYYYMMDD_HHMMSS.json
```

### 3. Revert Code
```bash
git reset --hard 4d39bbc
```

### 4. Restart Server
```bash
sudo systemctl start gunicorn
```

---

## 📊 What Changed

### Database:
- ✅ Added `approval_recorded_at` field to Loan model
- ✅ Added `disbursement_recorded_at` field to Loan model
- ✅ Updated existing loans to have backdated dates
- ✅ Regenerated payment schedules

### Code:
- ✅ Loan approval now uses backdated application date
- ✅ Loan disbursement can accept backdated date
- ✅ Payment schedules calculated from backdated dates

### Reports:
- ✅ Loans now show correct historical dates
- ✅ Vault reports show accurate historical data
- ✅ Payment schedules have correct due dates

---

## 🆘 Troubleshooting

### Issue: Migration Fails
```bash
# Check migration status
python manage.py showmigrations loans

# If 0999 conflicts, rename it
cd loans/migrations
mv 0999_add_audit_timestamps.py 0100_add_audit_timestamps.py

# Edit the file and update dependencies
# Then run migrate again
python manage.py migrate loans
```

### Issue: Fix Script Shows Errors
- Check the error message
- Most errors are non-fatal
- Script continues with other loans
- Can re-run to fix any that failed

### Issue: Server Won't Start
```bash
# Check logs
sudo journalctl -u gunicorn -n 100

# Check for Python errors
python manage.py check

# Try running manually
python manage.py runserver
```

### Issue: Dates Still Look Wrong
- Run fix script again: `python manage.py fix_backdated_loans`
- Check specific loan in Django shell
- Contact support with loan number

---

## 📞 Support

If you encounter issues:

1. **Check logs**: `sudo journalctl -u gunicorn -n 100`
2. **Check database backup exists**: `ls -lh backup_before_backdating_*.json`
3. **Take screenshots** of any errors
4. **Note which step failed**

---

## ✅ Success Criteria

Deployment is successful if:
- [ ] Migration completed without errors
- [ ] Fix script completed without errors
- [ ] Server restarted successfully
- [ ] Website loads correctly
- [ ] Backdated loans show correct dates
- [ ] Payment schedules look correct
- [ ] No errors in logs

---

**Deployment Date**: _____________  
**Deployed By**: _____________  
**Commit**: c4026f6  
**Status**: ⬜ Pending / ⬜ Success / ⬜ Rolled Back
