# Deployment Checklist - May 22, 2026

## Summary of Changes Ready for Deployment

All code changes have been completed and pushed to GitHub. The production server has pulled the latest code, but **the server needs to be restarted** for changes to take effect.

---

## ✅ COMPLETED TASKS

### 1. **Processing Fee Transaction Type Fix**
- **Issue**: Processing fees showing as "Cash Deposit" instead of "Processing Fee" in vault
- **Files Changed**:
  - `loans/views_application.py` (line 576)
  - `clients/views.py` (line 1489)
- **Script Created**: `expenses/management/commands/fix_processing_fee_transactions.py`
- **Production Status**: 
  - ✅ Script run successfully
  - ✅ 11 transactions updated (K1,900.00 total)
  - ⚠️ Server NOT restarted - new code not active yet

### 2. **Full Backdating for Loans**
- **Issue**: Backdated loans showing today's date instead of backdated application date
- **Files Changed**:
  - `loans/models.py` - Added `approval_recorded_at` and `disbursement_recorded_at` fields
  - `loans/views_application.py` - Uses backdated application date for loan creation
  - `loans/views.py` - Accepts optional `disbursement_date` parameter for backdating
- **Migration**: `loans/migrations/0999_add_audit_timestamps.py`
- **Script Created**: 
  - `loans/management/commands/add_audit_columns.py` (adds columns via SQL)
  - `loans/management/commands/fix_backdated_loans.py` (fixes existing loans)
- **Production Status**:
  - ✅ Database columns added successfully
  - ✅ Fix script run: 101 applications checked, all already aligned
  - ⚠️ Server NOT restarted - new code not active yet

### 3. **Act As Officer Feature - Disbursement Fix**
- **Issue**: Manager acting as officer gets "Only loan officers can disburse loans" error
- **Files Changed**:
  - `loans/views.py` (DisburseLoanView.post() - lines 574-578)
  - `templates/loans/detail_tailwind.html` (line 389 - disburse button condition)
- **Changes**:
  - Backend now checks for `acting_as_officer` in addition to `user.role == 'loan_officer'`
  - Template now shows disburse button when manager is acting as officer
  - Audit trail added to loan notes when disbursing on behalf of officer
- **Production Status**:
  - ✅ Code changes complete
  - ⚠️ Server NOT restarted - new code not active yet

---

## 🔄 DEPLOYMENT STEPS

### Step 1: Restart the Server
```bash
# SSH into production server
ssh iwnd349@ipanel2

# Navigate to project directory
cd ~/www/palmcashloans.site

# Restart the Django application
# (Use your specific restart command - e.g., systemctl, supervisorctl, or touch wsgi.py)
touch palmcash/wsgi.py
# OR
sudo systemctl restart palmcash
# OR
sudo supervisorctl restart palmcash
```

### Step 2: Verify Changes

#### Test 1: Processing Fees in Vault
1. Go to Vault Transactions
2. Filter by transaction type "Processing Fee"
3. Verify new processing fees show correct type (not "Cash Deposit")

#### Test 2: Backdated Loans
1. Create a new loan application with yesterday's date
2. Have manager approve it
3. Verify the loan detail page shows yesterday's date (not today)
4. Check that `application_date` matches the backdated date

#### Test 3: Act As Officer - Disbursement
1. Login as Manager (Precious Nyawo)
2. Go to Manage Officers
3. Click "Act As Officer" for Mostine Lunda
4. Navigate to an approved loan (e.g., LV-000126)
5. Verify "Disburse Loan" button is visible
6. Click "Disburse Loan"
7. Verify disbursement succeeds (no "Only loan officers can disburse" error)
8. Check loan notes for audit trail: "Disbursed by [Manager Name] on behalf of [Officer Name]"

---

## 📊 DATABASE CHANGES SUMMARY

### New Columns Added
- `loans_loan.approval_recorded_at` (datetime, nullable)
- `loans_loan.disbursement_recorded_at` (datetime, nullable)

### Data Fixed
- 11 vault transactions updated from `transaction_type='deposit'` to `transaction_type='processing_fee'`
- Total amount: K1,900.00
- Branches affected: KUKU (5), MANDEVU BRANCH (2), KAMWALA SOUTH (2), Chazanga (2)

---

## 🐛 KNOWN ISSUES (RESOLVED)

### Issue 1: Manager Acting as Officer Cannot Disburse
- **Status**: ✅ FIXED
- **Solution**: Updated `DisburseLoanView.post()` to check for `acting_as_officer`
- **Solution**: Updated template to show disburse button when acting as officer

### Issue 2: Backdated Loans Show Today's Date
- **Status**: ✅ FIXED
- **Solution**: Updated loan creation to use backdated application date
- **Solution**: Added audit timestamp fields to track system vs business dates

### Issue 3: Processing Fees Show as Cash Deposits
- **Status**: ✅ FIXED
- **Solution**: Changed `transaction_type='deposit'` to `transaction_type='processing_fee'`
- **Solution**: Fixed 11 existing transactions in database

---

## 📝 POST-DEPLOYMENT NOTES

### For Managers
- When acting as an officer, you can now disburse loans on their behalf
- All actions are recorded in the loan notes with your name and the officer's name
- The global banner shows who you're acting as
- Click "Stop Acting" to return to your normal manager view

### For Loan Officers
- No changes to your workflow
- Backdated loans will now show the correct application date
- Processing fees will show correctly in vault transactions

### For Admins
- Monitor the audit trail in loan notes for "acted on behalf of" entries
- Check vault transactions to ensure processing fees are categorized correctly
- Review backdated loans to ensure dates are accurate

---

## 🔍 VERIFICATION QUERIES

### Check Processing Fee Transactions
```sql
SELECT 
    id,
    branch,
    transaction_type,
    amount,
    description,
    created_at
FROM expenses_vaulttransaction
WHERE transaction_type = 'processing_fee'
ORDER BY created_at DESC
LIMIT 20;
```

### Check Backdated Loans
```sql
SELECT 
    application_number,
    application_date,
    approval_date,
    approval_recorded_at,
    disbursement_date,
    disbursement_recorded_at,
    status
FROM loans_loan
WHERE approval_recorded_at IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;
```

### Check Act As Officer Audit Trail
```sql
SELECT 
    application_number,
    notes,
    status,
    loan_officer_id
FROM loans_loan
WHERE notes LIKE '%on behalf of%'
ORDER BY updated_at DESC
LIMIT 10;
```

---

## ⚠️ CRITICAL REMINDER

**THE SERVER MUST BE RESTARTED FOR ALL CHANGES TO TAKE EFFECT!**

Without a restart:
- Processing fees will continue to show as "Cash Deposit"
- Backdated loans will show today's date
- Managers acting as officers will get disbursement errors

After restart, all three issues will be resolved.

---

## 📞 SUPPORT

If you encounter any issues after deployment:
1. Check the server logs for errors
2. Verify the database changes were applied correctly
3. Ensure the latest code was pulled from GitHub
4. Confirm the server was restarted properly

---

**Last Updated**: May 22, 2026
**Deployment Status**: Ready - Awaiting Server Restart
