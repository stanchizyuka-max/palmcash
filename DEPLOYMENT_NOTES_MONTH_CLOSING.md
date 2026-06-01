# Deployment Notes: Month Closing History & Security Reset

## Date: June 1, 2026

## Summary
Fixed two critical issues with the month closing functionality:
1. **History not showing**: Month closings were not appearing in the history page
2. **Securities not resetting**: Security deposits were not being reset to K0.00 on month close

## Changes Made

### Backend Changes:
1. **dashboard/vault_views.py**
   - `vault_month_close()`: Added security deposit reset functionality
   - `vault_month_history()`: Fixed transaction grouping to properly display closings

### Frontend Changes:
1. **dashboard/templates/dashboard/vault_month_close.html**
   - Updated UI to show security reset information
   - Changed layout to 2x2 grid showing all balances to be closed

2. **dashboard/templates/dashboard/vault_month_history.html**
   - Updated to show breakdown of daily/weekly vault amounts
   - Added security reset amount display

## Deployment Steps

### 1. Backup Database
```bash
mysqldump -u root -p palmcash_db > backup_before_month_closing_fix_$(date +%Y%m%d).sql
```

### 2. Pull Latest Code
```bash
cd /var/www/iwnd349/data/www/palmcashloans.site
git pull origin main
```

### 3. No Database Migrations Required
No schema changes were made. The fix only modifies:
- Business logic in views
- Template display
- Uses existing VaultTransaction and SecurityDeposit models

### 4. Restart Application
```bash
# If using systemd
sudo systemctl restart palmcash

# If using supervisor
sudo supervisorctl restart palmcash

# If using gunicorn directly
pkill -HUP gunicorn
```

### 5. Clear Cache (if applicable)
```bash
python manage.py clear_cache
# or
redis-cli FLUSHALL  # if using Redis
```

## Testing After Deployment

### Test 1: View Existing History
1. Navigate to: Dashboard → Vault → View History
2. **Expected**: Should see all previously closed months
3. **Expected**: "Total Closings" should show correct count (not 0)
4. **Expected**: Each closing should show daily/weekly breakdown

### Test 2: Close a New Month
1. Navigate to: Dashboard → Vault → Close Month
2. Select a branch (if admin)
3. **Expected**: Should see 4 cards:
   - Daily Vault balance
   - Weekly Vault balance
   - Security Deposits (Will Reset to K0.00)
   - Total Vault balance
4. Click "Close Month & Reset Vaults + Securities"
5. **Expected**: Success message showing all reset amounts
6. **Expected**: Vault balances = K0.00
7. **Expected**: Security deposits = K0.00

### Test 3: Verify Security Reset
```sql
-- Before closing month, check security deposits
SELECT loan_id, paid_amount FROM loans_securitydeposit 
WHERE is_verified = TRUE;

-- After closing month, verify they're reset
SELECT loan_id, paid_amount FROM loans_securitydeposit 
WHERE is_verified = TRUE;
-- All paid_amount should be 0.00
```

### Test 4: Verify Transactions Created
```sql
-- Check that 3 transactions were created for the closing
SELECT 
    transaction_type,
    vault_type,
    amount,
    description,
    reference_number
FROM expenses_vaulttransaction
WHERE transaction_type = 'month_close'
AND description LIKE '%2026-06%'  -- Replace with your closing month
ORDER BY transaction_date DESC;

-- Should see 3 records:
-- 1. Daily vault closing
-- 2. Weekly vault closing
-- 3. Security deposits closing
```

### Test 5: Verify History Display
1. Navigate to: Dashboard → Vault → View History
2. **Expected**: New closing appears at top of list
3. **Expected**: Shows breakdown of daily and weekly amounts
4. **Expected**: Shows security reset amount
5. **Expected**: Filter by month works correctly

## Rollback Plan

If issues occur, rollback is simple since no schema changes were made:

### Option 1: Git Revert
```bash
cd /var/www/iwnd349/data/www/palmcashloans.site
git revert HEAD
sudo systemctl restart palmcash
```

### Option 2: Restore Specific Files
```bash
cd /var/www/iwnd349/data/www/palmcashloans.site
git checkout HEAD~1 -- dashboard/vault_views.py
git checkout HEAD~1 -- dashboard/templates/dashboard/vault_month_close.html
git checkout HEAD~1 -- dashboard/templates/dashboard/vault_month_history.html
sudo systemctl restart palmcash
```

### Option 3: Database Restore (if data corruption)
```bash
mysql -u root -p palmcash_db < backup_before_month_closing_fix_YYYYMMDD.sql
```

## Known Limitations

1. **Historical Data**: Closings made before this fix will only show 2 transactions (daily, weekly) - no security transaction. This is expected and won't cause errors.

2. **Security Reset**: Only affects **verified** security deposits (`is_verified=True`). Unverified deposits are not reset.

3. **Grouping Logic**: History grouping relies on description format. If description format changes, grouping may break.

## Monitoring

After deployment, monitor for:

1. **Error Logs**: Check for any exceptions in month closing
```bash
tail -f /var/log/palmcash/error.log | grep "Month close error"
```

2. **Transaction Count**: Verify 3 transactions per closing
```sql
SELECT 
    DATE(transaction_date) as closing_date,
    COUNT(*) as transaction_count
FROM expenses_vaulttransaction
WHERE transaction_type = 'month_close'
GROUP BY DATE(transaction_date)
HAVING transaction_count != 3;
-- Should return no rows (all closings should have 3 transactions)
```

3. **Security Reset**: Verify securities are actually resetting
```sql
SELECT 
    COUNT(*) as non_zero_securities
FROM loans_securitydeposit
WHERE is_verified = TRUE 
AND paid_amount > 0;
-- After month close, this should be 0
```

## Support

If issues arise:
1. Check error logs first
2. Verify database transactions were created
3. Check that security deposits were reset
4. Contact development team with:
   - Error messages
   - Branch name
   - Closing month attempted
   - Screenshots of issue

## Success Criteria

Deployment is successful when:
- ✅ History page shows all previous closings (Total Closings > 0)
- ✅ New month close creates 3 transactions
- ✅ Vault balances reset to K0.00
- ✅ Security deposits reset to K0.00
- ✅ History displays breakdown correctly
- ✅ No errors in logs
- ✅ Users can filter history by month
- ✅ Users can close months for all branches

## Documentation

Full technical documentation: `MONTH_CLOSING_HISTORY_AND_SECURITY_RESET_FIX.md`
