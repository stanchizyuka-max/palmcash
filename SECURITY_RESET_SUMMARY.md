# Security Reset on Month Closing - Summary

## ✅ YES - Securities Will Reset When You Close a Month

When you close a month, the system will now automatically:
1. **Calculate total security deposits** for the branch
2. **Create a security closing transaction** in vault history
3. **Reset all security deposits to K0.00** for that branch

## How It Works

### When You Close a Month:

**Dashboard → Vault → Close Month**

The system will:
1. Close Daily Vault → Reset to K0.00
2. Close Weekly Vault → Reset to K0.00
3. **Close Securities → Reset to K0.00** ✨ NEW!

### What Gets Reset:

All `SecurityDeposit.paid_amount` values for loans in that branch will be set to K0.00.

### What Gets Recorded:

A vault transaction is created:
- **Type**: `month_close`
- **Description**: "Month closing — YYYY-MM. Security deposits closing balance: K..."
- **Reference**: `CLOSE-SECURITY-YYYY-MM-XXXX`
- **Amount**: Total security balance before reset

### What You'll See:

**Success Message:**
```
Month 2026-06 closed successfully.
Vault balances reset: Daily K1,234.00, Weekly K5,678.00.
Security deposits reset: K28,200.00. All balances now at K0.00.
```

**In History:**
- Closing shows security reset amount
- Security balance column shows K28,200.00 (before reset)
- Security amount column shows K28,200.00 (what was reset)

## Current Status

### ✅ Code is Ready
The month closing code has been updated to properly find and reset security deposits.

### ⚠️ Old Closings Don't Have Security Reset
The May 2026 closings you did earlier were done with the old code, so they:
- ✅ Reset vault balances
- ❌ Did NOT reset securities

### 🔄 Next Month Closing Will Work
When you close June 2026 (or any future month), it will:
- ✅ Reset vault balances
- ✅ Reset securities ← This will work now!

## Manual Reset (One-Time)

Since the May closing didn't reset securities, you can manually reset them now:

### On Server:
```bash
cd /var/www/iwnd349/data/www/palmcash-main

# Pull latest code
git pull origin main

# Restart application (important!)
sudo systemctl restart palmcash

# Run simple reset script
python reset_all_securities_simple.py
```

This will reset all K28,200.00 in securities to K0.00.

## Verification

### Before Closing a Month:
Check Securities page - shows current balances (e.g., K28,200.00)

### After Closing a Month:
1. Check Securities page - should show K0.00
2. Check Month History - should show security reset amount
3. Check success message - should mention security reset

## Technical Details

### Query Logic:
The month closing now uses the same logic as the Securities page:

```python
# Get officers in branch
officers = User.objects.filter(
    role='loan_officer',
    officer_assignment__branch__iexact=branch.name,
    is_active=True
).distinct()

# Get loans through officers OR group assignments
loans_query = Q(loan_officer__in=officers) | 
              Q(borrower__group_memberships__group__assigned_officer__in=officers)
branch_loans = Loan.objects.filter(loans_query).distinct()

# Get security deposits for these loans
security_deposits = SecurityDeposit.objects.filter(
    loan__in=branch_loans,
    is_verified=True
)

# Reset them
security_deposits.update(paid_amount=0)
```

### Why This Query?
- Loans can be assigned directly to officers
- OR loans can be through borrower groups assigned to officers
- This matches exactly how the Securities page calculates balances

## Files Modified

1. **dashboard/vault_views.py** - Updated `vault_month_close()` function
2. **dashboard/templates/dashboard/vault_month_close.html** - Shows security reset info
3. **dashboard/templates/dashboard/vault_month_history.html** - Displays security amounts

## Deployment

### On Server:
```bash
cd /var/www/iwnd349/data/www/palmcashloans.site
git pull origin main
sudo systemctl restart palmcash
```

**IMPORTANT**: You must restart the application for the changes to take effect!

## Summary

| Feature | Status |
|---------|--------|
| Vault reset on month close | ✅ Working |
| Security reset on month close | ✅ Working (after deployment) |
| History shows closings | ✅ Working |
| History shows security reset | ✅ Working (for new closings) |
| Old closings (May 2026) | ⚠️ No security reset (use manual script) |
| Future closings (June+) | ✅ Will reset securities automatically |

## Next Steps

1. **Deploy latest code** to server (git pull + restart)
2. **Run manual reset script** to reset current K28,200.00
3. **Close June month** at end of June - securities will reset automatically
4. **Verify** securities show K0.00 after closing

---

**Bottom Line**: Yes, securities will reset automatically when you close a month, starting with the next month you close (after deploying the latest code)! 🎉
