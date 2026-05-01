# 🚀 Dual-Vault System - Deployment Steps

## ⚠️ CRITICAL: Read This First!

This deployment will transform your single-vault system into a dual-vault system. **The system will be temporarily unavailable during deployment.**

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### **1. Backup Everything**
```bash
# On server
cd ~/www/palmcashloans.site

# Backup database
mysqldump -u your_user -p palmcash_db > backup_before_dual_vault_$(date +%Y%m%d_%H%M%S).sql

# Backup code
tar -czf code_backup_$(date +%Y%m%d_%H%M%S).tar.gz .
```

### **2. Verify Git Status**
```bash
# Make sure all changes are committed
git status
git add .
git commit -m "Dual-vault system implementation"
git push origin main
```

### **3. Schedule Maintenance Window**
- **Recommended:** Off-peak hours (e.g., 11 PM - 1 AM)
- **Duration:** 30-60 minutes
- **Notify:** All users in advance

---

## 🔧 DEPLOYMENT STEPS (On Server)

### **Step 1: Pull Latest Code**
```bash
cd ~/www/palmcashloans.site
git pull origin main
```

### **Step 2: Activate Virtual Environment**
```bash
source .venv/bin/activate
```

### **Step 3: Run Migrations**
```bash
# This creates DailyVault and WeeklyVault tables
python manage.py migrate loans 0099
python manage.py migrate expenses 0008

# Verify migrations
python manage.py showmigrations loans
python manage.py showmigrations expenses
```

### **Step 4: Analyze Current Data**
```bash
# This shows what will be migrated (READ-ONLY)
python manage.py migrate_to_dual_vault --analyze
```

**Review the output carefully!** It will show:
- How many branches will get dual vaults
- Current vault balances
- How transactions will be split
- Any potential issues

### **Step 5: Migrate Data**
```bash
# This actually migrates the data
python manage.py migrate_to_dual_vault --migrate

# Expected output:
# ✓ Created Daily Vault for Branch X (Balance: K...)
# ✓ Created Weekly Vault for Branch X (Balance: K...)
# ✓ Migrated X transactions
```

### **Step 6: Validate Migration**
```bash
# This verifies everything worked correctly
python manage.py migrate_to_dual_vault --validate

# Expected output:
# ✓ All branches have dual vaults
# ✓ All transactions have vault_type
# ✓ Balances match
```

### **Step 7: Restart Application**
```bash
# Restart Django/Gunicorn
sudo systemctl restart gunicorn
# OR
sudo systemctl restart palmcash

# Restart Nginx (if needed)
sudo systemctl restart nginx
```

### **Step 8: Verify System is Working**
```bash
# Check logs for errors
tail -f /var/log/gunicorn/error.log
# OR
tail -f /var/log/palmcash/error.log
```

---

## ✅ POST-DEPLOYMENT TESTING

### **Test 1: View Dashboards**
1. Login as Manager
2. Check dashboard shows both Daily and Weekly vaults
3. Verify balances are correct

### **Test 2: Disburse Daily Loan**
1. Create/approve a daily loan
2. Disburse it
3. Verify Daily Vault balance decreased
4. Verify Weekly Vault balance unchanged

### **Test 3: Disburse Weekly Loan**
1. Create/approve a weekly loan
2. Disburse it
3. Verify Weekly Vault balance decreased
4. Verify Daily Vault balance unchanged

### **Test 4: Collect Daily Payment**
1. Record a daily loan payment
2. Verify Daily Vault balance increased
3. Verify Weekly Vault balance unchanged

### **Test 5: Collect Weekly Payment**
1. Record a weekly loan payment
2. Verify Weekly Vault balance increased
3. Verify Daily Vault balance unchanged

### **Test 6: Bank Operations**
1. Try bank deposit (should ask which vault)
2. Try bank withdrawal (should ask which vault)
3. Verify correct vault is updated

---

## 🚨 ROLLBACK PROCEDURE (If Something Goes Wrong)

### **Option 1: Restore Database**
```bash
# Stop application
sudo systemctl stop gunicorn

# Restore database
mysql -u your_user -p palmcash_db < backup_before_dual_vault_YYYYMMDD_HHMMSS.sql

# Revert code
git reset --hard HEAD~1

# Restart application
sudo systemctl start gunicorn
```

### **Option 2: Revert Migrations**
```bash
# Revert to previous migration
python manage.py migrate loans 0019
python manage.py migrate expenses 0007

# Restart application
sudo systemctl restart gunicorn
```

---

## 📊 WHAT CHANGED?

### **Database Changes**
- ✅ Created `loans_dailyvault` table
- ✅ Created `loans_weeklyvault` table
- ✅ Added `vault_type` column to `expenses_vaulttransaction`
- ✅ Renamed `branch.vault` to `branch.vault_legacy`
- ✅ Added `branch.daily_vault` relationship
- ✅ Added `branch.weekly_vault` relationship

### **Code Changes**
- ✅ Created `loans/vault_services_dual.py` (new service layer)
- ✅ Updated all views to use dual-vault services
- ✅ Updated all templates to show both vaults
- ✅ Updated forms to include vault selection
- ✅ All loan operations now route to correct vault automatically
- ✅ All bank operations now require vault selection

### **Business Logic Changes**
- ✅ Daily loans → Daily Vault only
- ✅ Weekly loans → Weekly Vault only
- ✅ No mixing of funds between vaults
- ✅ Each vault maintains independent balance
- ✅ Reports separated by vault type

---

## 📞 SUPPORT CONTACTS

**If you encounter issues:**
1. Check error logs first
2. Try rollback procedure
3. Contact technical support

---

## 📝 DEPLOYMENT LOG

**Date:** _________________
**Performed by:** _________________
**Start time:** _________________
**End time:** _________________

**Checklist:**
- [ ] Database backup created
- [ ] Code backup created
- [ ] Users notified
- [ ] Migrations run successfully
- [ ] Data migrated successfully
- [ ] Validation passed
- [ ] Application restarted
- [ ] Post-deployment tests passed
- [ ] No errors in logs
- [ ] System operational

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

**Sign-off:** _________________

---

## 🎯 EXPECTED RESULTS

After successful deployment:
- ✅ Each branch has 2 vaults (Daily + Weekly)
- ✅ Daily loans use Daily Vault
- ✅ Weekly loans use Weekly Vault
- ✅ Dashboards show both vault balances
- ✅ Bank operations ask which vault to use
- ✅ All existing data preserved and correctly categorized
- ✅ No data loss
- ✅ System fully operational

---

**IMPORTANT:** Keep this document and the backup files for at least 30 days after deployment!
