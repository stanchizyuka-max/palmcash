# Troubleshooting: Month Closing History Shows 0

## Problem
The month closing history page shows "Total Closings: 0" even though you've closed months for all branches.

## Possible Causes

### 1. Code Not Deployed to Server ⚠️ MOST LIKELY
The fix was pushed to GitHub but not pulled and deployed on the server.

**How to Check:**
```bash
# SSH into server
ssh your-server

# Navigate to project directory
cd /var/www/iwnd349/data/www/palmcashloans.site

# Check current git commit
git log -1 --oneline

# Should show: "Fix month closing history display and add security deposit reset"
# If it shows an older commit, the code is not deployed
```

**How to Fix:**
```bash
# Pull latest code
git pull origin main

# Restart application
sudo systemctl restart palmcash
# OR
sudo supervisorctl restart palmcash
# OR
pkill -HUP gunicorn

# Clear cache if applicable
python manage.py clear_cache
```

### 2. No Month Closings Were Actually Created
The month closing transactions were never created in the database.

**How to Check:**
```bash
# Run diagnostic script on server
cd /var/www/iwnd349/data/www/palmcashloans.site
python diagnose_month_closings.py
```

**What to Look For:**
- If it shows "NO month_close transactions found" → No closings were created
- If it shows transactions but with wrong format → Description format issue

**How to Fix:**
- Try closing a month manually through the UI
- The new code will create properly formatted transactions

### 3. Old Transaction Format
Closings were created with old code that used different description format.

**How to Check:**
Look at the diagnostic script output for transactions with non-standard format.

**How to Fix:**
Run this SQL to update old transaction descriptions:

```sql
-- Check current descriptions
SELECT id, branch, description, transaction_date
FROM expenses_vaulttransaction
WHERE transaction_type = 'month_close'
ORDER BY transaction_date DESC;

-- If descriptions don't match "Month closing — YYYY-MM" format,
-- they need to be updated manually or recreated
```

### 4. Application Server Not Restarted
Code was pulled but the application server wasn't restarted, so it's still running old code.

**How to Check:**
```bash
# Check when the Python process started
ps aux | grep gunicorn
# OR
ps aux | grep python

# If the process started before you pulled the code, it needs restart
```

**How to Fix:**
```bash
# Restart the application
sudo systemctl restart palmcash
```

## Step-by-Step Troubleshooting

### Step 1: Verify Code Deployment
```bash
# SSH into server
ssh your-server

# Navigate to project
cd /var/www/iwnd349/data/www/palmcashloans.site

# Check if latest code is present
python check_server_code_version.py
```

**Expected Output:**
```
✅ ALL NEW FEATURES DETECTED
The server appears to have the latest code.
```

**If you see "❌ MISSING FEATURES DETECTED":**
```bash
git pull origin main
sudo systemctl restart palmcash
```

### Step 2: Check Database for Transactions
```bash
# Run diagnostic script
python diagnose_month_closings.py
```

**Scenario A: "NO month_close transactions found"**
- This means no months were ever closed
- Solution: Close a month through the UI to create transactions

**Scenario B: "Found X month_close transactions"**
- Transactions exist but history page shows 0
- Check if descriptions match format: "Month closing — YYYY-MM"
- If format is wrong, transactions won't be grouped correctly

**Scenario C: "Found X transactions, Y have proper format"**
- Some transactions have wrong format
- Old transactions won't appear in history
- New closings will work correctly

### Step 3: Test with New Month Closing
```bash
# After deploying code and restarting server:
# 1. Go to Dashboard → Vault → Close Month
# 2. Select a branch
# 3. Close the current month
# 4. Check if it appears in history
```

**What Should Happen:**
1. Success message shows vault and security reset amounts
2. 3 transactions created (daily, weekly, security)
3. History page shows the new closing
4. Total Closings count increases by 1

### Step 4: Verify Application Restart
```bash
# Check application logs for restart
sudo journalctl -u palmcash -n 50

# OR check gunicorn logs
tail -f /var/log/palmcash/gunicorn.log

# Look for startup messages indicating restart
```

## Quick Fix Commands

### If Code Not Deployed:
```bash
cd /var/www/iwnd349/data/www/palmcashloans.site
git pull origin main
sudo systemctl restart palmcash
# Wait 10 seconds
# Refresh browser and check history page
```

### If No Transactions Exist:
```bash
# Just close a month through the UI
# Dashboard → Vault → Close Month
# Select branch → Close Month & Reset Vaults + Securities
```

### If Application Not Restarted:
```bash
sudo systemctl restart palmcash
# OR
sudo supervisorctl restart palmcash
# OR
pkill -HUP gunicorn
```

## Verification Checklist

After applying fixes, verify:

- [ ] Latest git commit shows on server: `git log -1 --oneline`
- [ ] Application was restarted: Check process start time
- [ ] Diagnostic script shows transactions exist
- [ ] History page shows correct count
- [ ] Can close a new month successfully
- [ ] New closing appears in history immediately
- [ ] Security deposits reset to K0.00

## Common Mistakes

### ❌ Mistake 1: Only Pulled Code, Didn't Restart
```bash
git pull origin main  # ✅ Correct
# ❌ FORGOT TO RESTART!
```

**Fix:**
```bash
sudo systemctl restart palmcash  # ✅ Must restart!
```

### ❌ Mistake 2: Restarted Wrong Service
```bash
sudo systemctl restart nginx  # ❌ Wrong service!
```

**Fix:**
```bash
sudo systemctl restart palmcash  # ✅ Correct service
```

### ❌ Mistake 3: Pulled on Local Machine, Not Server
```bash
# On local machine:
git pull origin main  # ❌ This doesn't update the server!
```

**Fix:**
```bash
# SSH into server first:
ssh your-server
cd /var/www/iwnd349/data/www/palmcashloans.site
git pull origin main  # ✅ Pull on server
sudo systemctl restart palmcash
```

## Still Not Working?

If history still shows 0 after all steps:

### 1. Check Browser Cache
- Hard refresh: Ctrl + Shift + R (Windows) or Cmd + Shift + R (Mac)
- Or open in incognito/private window

### 2. Check Database Connection
```bash
python manage.py dbshell
```

```sql
-- Check if table exists
SHOW TABLES LIKE 'expenses_vaulttransaction';

-- Check transaction count
SELECT COUNT(*) FROM expenses_vaulttransaction 
WHERE transaction_type = 'month_close';

-- If count > 0 but history shows 0, it's a code issue
-- If count = 0, no closings were created
```

### 3. Check for Python Errors
```bash
# Check error logs
tail -f /var/log/palmcash/error.log

# Look for errors in vault_month_history view
grep "vault_month_history" /var/log/palmcash/error.log
```

### 4. Enable Debug Mode Temporarily
```python
# In settings.py (TEMPORARILY)
DEBUG = True

# Restart and check for detailed error messages
# REMEMBER TO SET DEBUG = False AFTER TROUBLESHOOTING
```

## Contact Support

If none of the above works, provide this information:

1. Output of `python check_server_code_version.py`
2. Output of `python diagnose_month_closings.py`
3. Output of `git log -1 --oneline`
4. Screenshot of history page showing 0 closings
5. Any error messages from logs

## Summary

**Most Common Solution (90% of cases):**
```bash
# On server:
cd /var/www/iwnd349/data/www/palmcashloans.site
git pull origin main
sudo systemctl restart palmcash
# Wait 10 seconds, then refresh browser
```

**If that doesn't work:**
1. Run diagnostic scripts
2. Check if transactions exist in database
3. Try closing a new month
4. Check application logs for errors
