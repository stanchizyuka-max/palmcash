# 🏦 Dual-Vault System Migration Guide

## Overview

This guide documents the migration from a single-vault system to a dual-vault system that separates Daily and Weekly loan operations.

---

## 🎯 Objectives

- **Separate** Daily and Weekly loan funds completely
- **Prevent** mixing of funds between loan types
- **Maintain** data integrity during migration
- **Zero** data loss or downtime

---

## 📊 Architecture Changes

### Before (Single Vault)
```
Branch
  └── BranchVault (single balance)
       └── All transactions mixed
```

### After (Dual Vault)
```
Branch
  ├── DailyVault (daily loan operations only)
  └── WeeklyVault (weekly loan operations only)
```

---

## 🔧 Migration Steps

### Step 1: Backup Database

```bash
# Create full backup
mysqldump -u username -p palmcash_db > backup_before_dual_vault_$(date +%Y%m%d).sql

# Verify backup
ls -lh backup_before_dual_vault_*.sql
```

### Step 2: Run Migrations

```bash
# Apply database schema changes
python manage.py migrate loans 0099_dual_vault_system
python manage.py migrate expenses 0008_add_vault_type_to_transactions
```

### Step 3: Analyze Current Data

```bash
# Dry-run analysis (no changes made)
python manage.py migrate_to_dual_vault --analyze
```

**Review the output carefully:**
- Current vault balances
- Loan distribution (daily vs weekly)
- Proposed balance split
- Transaction counts

### Step 4: Execute Migration

```bash
# Migrate all branches
python manage.py migrate_to_dual_vault --migrate

# OR migrate specific branch
python manage.py migrate_to_dual_vault --migrate --branch="MANDEVU"
```

### Step 5: Validate Results

```bash
# Run validation checks
python manage.py migrate_to_dual_vault --validate
```

**Validation checks:**
- ✓ Both vaults exist for each branch
- ✓ Balance reconciliation (old = daily + weekly)
- ✓ All transactions have vault_type assigned
- ✓ No orphaned records

---

## 📋 Pre-Migration Checklist

- [ ] Full database backup completed
- [ ] Staging environment tested
- [ ] Maintenance window scheduled
- [ ] Users notified of downtime
- [ ] Rollback plan prepared
- [ ] Analysis report reviewed

---

## 🔍 What Gets Migrated

### 1. Vault Models
- **BranchVault** → Renamed to `vault_legacy` (kept for reference)
- **DailyVault** → Created for each branch
- **WeeklyVault** → Created for each branch

### 2. Balances
- Legacy vault balance split based on loan disbursement ratio
- If no loans: 50/50 split
- If loans exist: Proportional to disbursements

### 3. Transactions
- Each `VaultTransaction` gets `vault_type` field
- Assigned based on `loan.repayment_frequency`
- Non-loan transactions default to 'weekly' (can be adjusted)

---

## 🎨 Balance Split Logic

```python
# Calculate disbursement ratio
daily_disbursed = sum(daily_loans.principal_amount)
weekly_disbursed = sum(weekly_loans.principal_amount)
total_disbursed = daily_disbursed + weekly_disbursed

# Split current balance proportionally
if total_disbursed > 0:
    daily_ratio = daily_disbursed / total_disbursed
    daily_vault_balance = current_balance * daily_ratio
    weekly_vault_balance = current_balance * (1 - daily_ratio)
else:
    # No loans yet - split 50/50
    daily_vault_balance = current_balance / 2
    weekly_vault_balance = current_balance / 2
```

---

## ⚠️ Important Notes

### Transaction Assignment Rules

1. **Loan-related transactions** → Assigned based on `loan.repayment_frequency`
2. **Non-loan transactions** → Default to 'weekly' vault
3. **Manual adjustments** → Can be made after migration if needed

### Legacy Vault

- **NOT deleted** - kept for audit trail
- Marked as `is_migrated=True`
- Relationship changed to `vault_legacy`
- Can be removed after 6 months of successful operation

### Rollback Plan

If migration fails:
```bash
# Restore from backup
mysql -u username -p palmcash_db < backup_before_dual_vault_YYYYMMDD.sql

# Revert migrations
python manage.py migrate loans 0098_auto_previous
python manage.py migrate expenses 0007_add_other_expense_code
```

---

## 🧪 Testing Checklist

After migration, test these scenarios:

### Daily Loans
- [ ] Disburse daily loan → Deducts from Daily Vault
- [ ] Collect daily payment → Credits to Daily Vault
- [ ] View daily vault balance
- [ ] Generate daily vault report

### Weekly Loans
- [ ] Disburse weekly loan → Deducts from Weekly Vault
- [ ] Collect weekly payment → Credits to Weekly Vault
- [ ] View weekly vault balance
- [ ] Generate weekly vault report

### Bank Operations
- [ ] Bank deposit to Daily Vault
- [ ] Bank deposit to Weekly Vault
- [ ] Bank withdrawal from Daily Vault
- [ ] Bank withdrawal from Weekly Vault

### Reports
- [ ] Vault balance report shows both vaults
- [ ] Transaction history filtered by vault type
- [ ] Month closing works for both vaults
- [ ] Dashboard displays both vault balances

---

## 📊 Sample Analysis Output

```
==================================================================
DUAL-VAULT MIGRATION ANALYSIS
==================================================================

----------------------------------------------------------------------
Branch: MANDEVU
----------------------------------------------------------------------
Current Vault Balance: K23,979.99

Loan Analysis:
  Daily Loans: 5
  Weekly Loans: 8

Disbursements:
  Daily: K5,000.00
  Weekly: K18,000.00
  Total: K23,000.00

Collections:
  Daily: K2,500.00
  Weekly: K9,000.00
  Total: K11,500.00

Net Position (Collections - Disbursements):
  Daily: K-2,500.00
  Weekly: K-9,000.00

Proposed Vault Split:
  Daily Vault: K5,212.17
  Weekly Vault: K18,767.82
  Total: K23,979.99

Vault Transactions:
  Total: 156
  Daily loan transactions: 45
  Weekly loan transactions: 98
  Non-loan transactions: 13
```

---

## 🚨 Troubleshooting

### Issue: Balance Mismatch After Migration

**Symptom:** `daily_vault + weekly_vault ≠ legacy_vault`

**Solution:**
```bash
# Check for rounding errors (< K0.01 is acceptable)
python manage.py migrate_to_dual_vault --validate

# If significant difference, investigate:
# 1. Check for transactions created during migration
# 2. Verify no concurrent operations occurred
# 3. Review transaction logs
```

### Issue: Transactions Missing vault_type

**Symptom:** Some transactions show `vault_type=NULL`

**Solution:**
```bash
# Re-run transaction migration
python manage.py migrate_to_dual_vault --migrate --branch="BRANCH_NAME"
```

### Issue: Cannot Access Vault After Migration

**Symptom:** Code still references old `branch.vault`

**Solution:**
- Update code to use `branch.daily_vault` or `branch.weekly_vault`
- See DUAL_VAULT_CODE_UPDATES.md for all required changes

---

## 📞 Support

If you encounter issues:

1. **Check validation output** for specific errors
2. **Review transaction logs** in database
3. **Consult backup** before making manual changes
4. **Document any manual adjustments** made

---

## ✅ Post-Migration Tasks

- [ ] Monitor system for 48 hours
- [ ] Verify all reports are accurate
- [ ] Train users on new vault interface
- [ ] Update documentation
- [ ] Schedule legacy vault cleanup (6 months)

---

## 📅 Timeline

- **Preparation:** 1 week
- **Migration:** 2-4 hours
- **Validation:** 1 hour
- **Monitoring:** 48 hours
- **Total:** ~1 week

---

## 🎓 Key Learnings

1. **Always backup** before major migrations
2. **Test on staging** with production data copy
3. **Validate thoroughly** before declaring success
4. **Monitor closely** for first 48 hours
5. **Document everything** for future reference

---

**Migration Date:** _____________
**Performed By:** _____________
**Validation Status:** _____________
**Notes:** _____________
