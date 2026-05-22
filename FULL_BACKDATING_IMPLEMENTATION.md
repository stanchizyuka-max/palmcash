# 🔄 Full Backdating Implementation

## Overview
This implementation enables complete backdating of loans from application through disbursement, while maintaining a proper audit trail with system timestamps.

---

## 🎯 What Changed

### Before (Inconsistent):
```
Application Date: Jan 15 (backdated)
Loan Created: May 22 (current) ❌
Approval Date: May 22 (current) ❌
Disbursement Date: May 22 (current) ❌
```

### After (Consistent):
```
Application Date: Jan 15 (backdated) ✅
Loan Created: Jan 15 (backdated) ✅
Approval Date: Jan 15 (backdated) ✅
Disbursement Date: Jan 20 (backdated) ✅

System Timestamps (Audit Trail):
- Approval Recorded At: May 22 (when manager clicked approve)
- Disbursement Recorded At: May 22 (when officer clicked disburse)
```

---

## 📝 Changes Made

### 1. **Loan Model** (`loans/models.py`)

Added two new fields for audit trail:

```python
# Audit Trail - System timestamps
approval_recorded_at = models.DateTimeField(
    null=True, 
    blank=True,
    help_text="System timestamp: when approval was recorded in the system"
)
disbursement_recorded_at = models.DateTimeField(
    null=True, 
    blank=True,
    help_text="System timestamp: when disbursement was recorded in the system"
)
```

**Purpose:**
- `approval_date` = Business date (when loan was actually approved - can be backdated)
- `approval_recorded_at` = System date (when manager clicked approve button)
- `disbursement_date` = Business date (when loan was actually disbursed - can be backdated)
- `disbursement_recorded_at` = System date (when officer clicked disburse button)

---

### 2. **Loan Approval View** (`loans/views_application.py`)

Updated `ApproveLoanApplicationView` to use backdated application date:

```python
# OLD CODE:
loan = Loan(
    # ... other fields
    approval_date=timezone.now(),  # Always current date
)
loan.save()

# NEW CODE:
loan = Loan(
    # ... other fields
    approval_date=loan_app.created_at,  # Use backdated application date
    approval_recorded_at=timezone.now(),  # System timestamp
)
loan._state.adding = False
loan.created_at = loan_app.created_at  # Backdate loan creation
loan.save()
```

**Result:**
- Loan is created with the same date as the application
- Approval date matches application date
- System timestamp records when manager actually approved

---

### 3. **Loan Disbursement View** (`loans/views.py`)

Updated `DisburseLoanView` to accept optional disbursement date:

```python
# Get disbursement date from POST data (for backdating)
disbursement_date_str = request.POST.get('disbursement_date')
if disbursement_date_str:
    disbursement_datetime = parse_and_convert(disbursement_date_str)
else:
    disbursement_datetime = timezone.now()

loan.disbursement_date = disbursement_datetime
loan.disbursement_recorded_at = timezone.now()  # System timestamp
```

**Result:**
- Disbursement can be backdated by passing `disbursement_date` in POST
- System timestamp records when officer actually disbursed
- Payment schedules calculated from backdated disbursement date

---

### 4. **Migration** (`loans/migrations/0999_add_audit_timestamps.py`)

Created migration to add new fields to existing database:

```python
operations = [
    migrations.AddField(
        model_name='loan',
        name='approval_recorded_at',
        field=models.DateTimeField(blank=True, null=True),
    ),
    migrations.AddField(
        model_name='loan',
        name='disbursement_recorded_at',
        field=models.DateTimeField(blank=True, null=True),
    ),
]
```

---

### 5. **Fix Script** (`loans/management/commands/fix_backdated_loans.py`)

Created management command to fix existing backdated loans:

```bash
# Preview changes
python manage.py fix_backdated_loans --dry-run

# Apply changes
python manage.py fix_backdated_loans

# Verbose output
python manage.py fix_backdated_loans --verbose
```

**What It Does:**
1. Finds all loans created from backdated applications
2. Updates loan `created_at` to match application date
3. Updates `approval_date` to match application date
4. Sets `approval_recorded_at` to original approval date (system timestamp)
5. Backdates `disbursement_date` proportionally
6. Sets `disbursement_recorded_at` to original disbursement date
7. Regenerates payment schedules based on new disbursement date
8. Provides detailed report of all changes

---

## 🚀 Deployment Steps

### Step 1: Backup Database
```bash
# On production server
cd /var/www/iwnd349/data/www/palmcashloans.site
python manage.py dumpdata > backup_before_backdating_$(date +%Y%m%d).json
```

### Step 2: Pull Latest Code
```bash
git pull origin main
```

### Step 3: Run Migration
```bash
python manage.py migrate loans
```

### Step 4: Preview Changes (Dry Run)
```bash
python manage.py fix_backdated_loans --dry-run --verbose
```

**Review the output carefully!** This shows what will be changed.

### Step 5: Apply Changes
```bash
python manage.py fix_backdated_loans
```

### Step 6: Restart Server
```bash
sudo systemctl restart gunicorn
```

---

## 📊 What Gets Fixed

### Example Scenario:

**Before Fix:**
```
Application:
  - application_number: LA-ABC12345
  - created_at: 2026-01-15 00:00:00 (backdated)
  - status: approved

Loan:
  - application_number: LV-000123
  - created_at: 2026-05-22 14:30:00 (current) ❌
  - approval_date: 2026-05-22 14:30:00 (current) ❌
  - disbursement_date: 2026-05-22 15:00:00 (current) ❌
  - status: active

Payment Schedule:
  - First payment due: 2026-05-23 ❌
  - Based on May 22 disbursement
```

**After Fix:**
```
Application:
  - application_number: LA-ABC12345
  - created_at: 2026-01-15 00:00:00 (backdated)
  - status: approved

Loan:
  - application_number: LV-000123
  - created_at: 2026-01-15 00:00:00 (backdated) ✅
  - approval_date: 2026-01-15 00:00:00 (backdated) ✅
  - approval_recorded_at: 2026-05-22 14:30:00 (system) ✅
  - disbursement_date: 2026-01-16 00:00:00 (backdated) ✅
  - disbursement_recorded_at: 2026-05-22 15:00:00 (system) ✅
  - status: active

Payment Schedule:
  - First payment due: 2026-01-17 ✅
  - Based on Jan 16 disbursement
  - REGENERATED with correct dates
```

---

## 🔍 Verification

### Check a Specific Loan:
```python
from loans.models import Loan, LoanApplication

# Find a backdated application
app = LoanApplication.objects.filter(
    created_at__lt='2026-05-01'
).first()

print(f"Application Date: {app.created_at}")

# Find its loan
loan = Loan.objects.filter(
    borrower=app.borrower,
    principal_amount=app.loan_amount
).first()

print(f"Loan Created: {loan.created_at}")
print(f"Approval Date: {loan.approval_date}")
print(f"Approval Recorded: {loan.approval_recorded_at}")
print(f"Disbursement Date: {loan.disbursement_date}")
print(f"Disbursement Recorded: {loan.disbursement_recorded_at}")

# Check payment schedule
from payments.models import PaymentSchedule
schedules = PaymentSchedule.objects.filter(loan=loan).order_by('due_date')
print(f"\nFirst Payment Due: {schedules.first().due_date}")
print(f"Last Payment Due: {schedules.last().due_date}")
```

---

## 📈 Impact on Reports

### Vault Reports:
- ✅ Processing fees appear on backdated application date
- ✅ Disbursements appear on backdated disbursement date
- ✅ Historical vault balances are accurate

### Loan Reports:
- ✅ Loans appear as created on backdated date
- ✅ Approval dates are backdated
- ✅ Disbursement dates are backdated
- ✅ Loan volume reports show correct historical data

### Payment Reports:
- ✅ Payment schedules calculated from backdated disbursement
- ✅ Due dates are correct
- ✅ Overdue calculations are accurate

### Audit Reports:
- ✅ System timestamps show when actions were actually performed
- ✅ Business dates show when events actually occurred
- ✅ Complete audit trail maintained

---

## ⚠️ Important Notes

### 1. Payment Schedules Are Regenerated
- Old payment schedules are deleted
- New schedules generated from backdated disbursement date
- **Existing payments are NOT affected**
- Only unpaid schedules are regenerated

### 2. Vault Transactions Are NOT Changed
- Processing fee transactions already use backdated dates
- Disbursement vault transactions keep their original dates
- This is intentional - vault transactions record when money actually moved

### 3. Completed Loans
- Completed loans are also fixed
- Payment schedules are regenerated
- Historical data becomes accurate

### 4. Active Loans
- Active loans are fixed
- Payment schedules are regenerated
- Borrowers may see different due dates
- **Communicate this to borrowers if needed**

---

## 🛡️ Safety Features

### Dry Run Mode:
```bash
python manage.py fix_backdated_loans --dry-run
```
- Shows exactly what will change
- No database modifications
- Safe to run multiple times

### Transaction Safety:
- Each loan fix is wrapped in a database transaction
- If any error occurs, changes are rolled back
- Database remains consistent

### Error Handling:
- Errors are logged but don't stop the script
- Summary shows how many succeeded/failed
- Can re-run to fix any that failed

---

## 📞 Troubleshooting

### Issue: Migration Fails
```bash
# Check current migrations
python manage.py showmigrations loans

# If migration number conflicts, rename it
mv loans/migrations/0999_add_audit_timestamps.py loans/migrations/0100_add_audit_timestamps.py

# Update dependency in migration file
# Then run migrate again
python manage.py migrate loans
```

### Issue: Script Finds No Loans to Fix
**Possible Reasons:**
1. All loans are already aligned with applications
2. No backdated applications exist
3. Loans were created before applications (shouldn't happen)

**Check:**
```bash
python manage.py fix_backdated_loans --dry-run --verbose
```

### Issue: Payment Schedules Look Wrong
**Check:**
1. Disbursement date is correct
2. Loan term (days/weeks) is correct
3. Repayment frequency is correct

**Regenerate manually:**
```python
from loans.models import Loan
from loans.utils import generate_payment_schedule

loan = Loan.objects.get(application_number='LV-000123')
loan.payment_schedule.all().delete()
generate_payment_schedule(loan)
```

---

## 📋 Checklist

### Before Deployment:
- [ ] Backup database
- [ ] Review code changes
- [ ] Test on staging/development environment
- [ ] Run dry-run on production to preview changes

### During Deployment:
- [ ] Pull latest code
- [ ] Run migration
- [ ] Run fix script with dry-run
- [ ] Review dry-run output
- [ ] Run fix script (live)
- [ ] Restart server

### After Deployment:
- [ ] Verify a few loans manually
- [ ] Check vault reports
- [ ] Check loan reports
- [ ] Check payment schedules
- [ ] Monitor for errors

---

## 🎉 Benefits

### For Users:
- ✅ Accurate historical data
- ✅ Correct payment schedules
- ✅ Proper loan timelines
- ✅ Accurate reports

### For Auditors:
- ✅ Clear audit trail
- ✅ Business dates vs system dates
- ✅ Complete transaction history
- ✅ Compliance-ready

### For System:
- ✅ Consistent data
- ✅ Accurate calculations
- ✅ Reliable reports
- ✅ Maintainable codebase

---

**Implementation Date**: May 22, 2026  
**Author**: Kiro AI Assistant  
**Status**: ✅ Ready for Deployment
