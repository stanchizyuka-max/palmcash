# Month Closing History & Security Reset Fix

## Issues Fixed

### Issue 1: Month Closing History Not Showing
**Problem**: User closed months for all branches but the history page showed "Total Closings: 0"

**Root Cause**: 
- The dual-vault system creates **3 separate transactions** per month close:
  1. Daily vault closing transaction
  2. Weekly vault closing transaction  
  3. Security deposits closing transaction (NEW)
- The history view was treating each transaction separately instead of grouping them by month
- This caused the display to be confusing and incomplete

**Solution**:
- Updated `vault_month_history()` function in `dashboard/vault_views.py` to:
  - Group transactions by month using `defaultdict`
  - Identify transaction type from description ("Daily vault", "Weekly vault", "Security deposits")
  - Combine all three transactions into a single closing record per month
  - Calculate total closing balance (daily + weekly)
  - Track security reset amount separately
  - Display all information in a unified view

### Issue 2: Securities Not Resetting on Month Close
**Problem**: User wanted security deposits to reset to K0.00 when closing a month (like vaults do)

**Root Cause**: 
- The month close function only reset vault balances
- Security deposits in the `SecurityDeposit` model were never touched
- No transaction was recorded for security resets

**Solution**:
- Updated `vault_month_close()` function in `dashboard/vault_views.py` to:
  - Calculate total security balance before reset
  - Create a closing transaction for securities
  - Reset all `SecurityDeposit.paid_amount` to 0 for the branch
  - Record the security closing in vault transactions
  - Show security reset in success message

## Files Modified

### 1. `dashboard/vault_views.py`

#### vault_month_close() function (lines ~590-680)
**Changes**:
- Added security deposit calculation before closing
- Added security closing transaction creation
- Reset all security deposits to K0.00 using `update(paid_amount=0)`
- Updated success message to include security reset amount
- Added proper error logging

**New Code**:
```python
# Calculate total security balance before reset
from django.db.models import Sum
security_deposits = SecurityDeposit.objects.filter(
    loan__branch=branch,
    is_verified=True
)
total_security_balance = security_deposits.aggregate(
    total=Sum('paid_amount')
)['total'] or 0

# ... (after vault closings)

# 3. Record security closing and reset all security deposits to zero
if total_security_balance > 0:
    VaultTransaction.objects.create(
        branch=branch.name,
        vault_type='daily',
        transaction_type='month_close',
        direction='out',
        amount=total_security_balance,
        balance_after=0,
        description=f'Month closing — {closing_month}. Security deposits closing balance: K{total_security_balance:,.2f}. {notes}'.strip(),
        reference_number=f'CLOSE-SECURITY-{closing_month}-{uuid.uuid4().hex[:4].upper()}',
        recorded_by=request.user,
        transaction_date=timezone.now(),
    )
    
    # Reset all security deposits to zero for this branch
    security_deposits.update(paid_amount=0)
```

#### vault_month_history() function (lines ~690-890)
**Changes**:
- Replaced linear transaction processing with grouped processing
- Added `defaultdict` to group transactions by month
- Added logic to identify transaction type from description
- Combined daily, weekly, and security transactions into single closing record
- Updated closing_list structure to include breakdown amounts
- Fixed available_months calculation to work with grouped data

**New Structure**:
```python
closing_groups = defaultdict(lambda: {
    'daily': None,
    'weekly': None,
    'security': None,
    'transaction_date': None,
    'recorded_by': None,
    'month': None,
})

# Group transactions by month
for closing in closings:
    month = extract_month_from_description(closing)
    
    if 'Daily vault' in closing.description:
        closing_groups[month]['daily'] = closing
    elif 'Weekly vault' in closing.description:
        closing_groups[month]['weekly'] = closing
    elif 'Security deposits' in closing.description:
        closing_groups[month]['security'] = closing

# Convert to unified closing records
for month, group in closing_groups.items():
    daily_amount = group['daily'].amount if group['daily'] else 0
    weekly_amount = group['weekly'].amount if group['weekly'] else 0
    security_amount = group['security'].amount if group['security'] else 0
    total_amount = daily_amount + weekly_amount
    
    closing_list.append({
        'month': month,
        'amount': total_amount,
        'daily_amount': daily_amount,
        'weekly_amount': weekly_amount,
        'security_amount': security_amount,
        # ... other fields
    })
```

### 2. `dashboard/templates/dashboard/vault_month_close.html`

**Changes**:
- Updated "Current Vault Balances" section to "Current Balances to be Closed"
- Changed from 3-column to 2x2 grid layout
- Added security deposits card showing "Will Reset to K0.00"
- Updated info message to mention security reset
- Updated button text to "Close Month & Reset Vaults + Securities"
- Updated confirmation dialog to mention security deposits

**New Display**:
```
┌─────────────┬─────────────┐
│ Daily Vault │Weekly Vault │
│   K1,234    │   K5,678    │
└─────────────┴─────────────┘
┌─────────────┬─────────────┐
│  Security   │ Total Vault │
│ Will Reset  │   K6,912    │
│  to K0.00   │             │
└─────────────┴─────────────┘
```

### 3. `dashboard/templates/dashboard/vault_month_history.html`

**Changes**:
- Updated closing balance column to show breakdown
- Added daily and weekly amounts as sub-items
- Updated security column to show reset amount
- Added "Reset: K..." text for security amounts

**New Display**:
```
Closing Balance:
  K6,912
  Daily: K1,234
  Weekly: K5,678

Security Held:
  K2,500
  Reset: K2,500
```

## How It Works Now

### Month Closing Process:
1. Admin/Manager selects branch and closing month
2. System calculates:
   - Daily vault balance
   - Weekly vault balance
   - Total security deposits for branch
3. System creates 3 transactions:
   - Daily vault closing (direction='out', amount=daily_balance)
   - Weekly vault closing (direction='out', amount=weekly_balance)
   - Security closing (direction='out', amount=total_security)
4. System resets:
   - Daily vault balance → K0.00
   - Weekly vault balance → K0.00
   - All SecurityDeposit.paid_amount → K0.00
5. Success message shows all reset amounts

### History Display Process:
1. Query all `transaction_type='month_close'` transactions
2. Group by month using description regex
3. Identify transaction type from description keywords
4. Combine into single record per month showing:
   - Total closing balance (daily + weekly)
   - Breakdown of daily and weekly amounts
   - Security reset amount
   - Period inflows/outflows
   - Savings balance
5. Display in table with all details

## Testing Checklist

### Month Close:
- [ ] Close month for a branch with vault balances
- [ ] Verify 3 transactions created (daily, weekly, security)
- [ ] Verify vault balances reset to K0.00
- [ ] Verify security deposits reset to K0.00
- [ ] Verify success message shows all amounts
- [ ] Try closing same month twice (should fail with error)

### History Display:
- [ ] View history page after closing
- [ ] Verify closing appears in list (Total Closings > 0)
- [ ] Verify closing shows correct total amount
- [ ] Verify breakdown shows daily and weekly amounts
- [ ] Verify security reset amount displays
- [ ] Filter by month and verify it works
- [ ] Switch branches and verify correct closings show

### Security Reset Verification:
- [ ] Check SecurityDeposit records before close
- [ ] Close month
- [ ] Check SecurityDeposit records after close (should be K0.00)
- [ ] Verify security closing transaction exists in VaultTransaction

## Database Impact

### VaultTransaction Table:
- **Before**: 2 transactions per month close (daily, weekly)
- **After**: 3 transactions per month close (daily, weekly, security)

### SecurityDeposit Table:
- **Before**: `paid_amount` retained across months
- **After**: `paid_amount` reset to 0 on month close

## Success Message Example

```
Month 2026-05 closed successfully.
Vault balances reset: Daily K1,234.50, Weekly K5,678.90.
Security deposits reset: K2,500.00. All balances now at K0.00.
```

## Notes

- Security reset only affects **verified** security deposits (`is_verified=True`)
- Security closing transaction uses `vault_type='daily'` (securities tracked in daily vault)
- History grouping uses regex pattern: `r'Month closing — ([\d-]+)'`
- Transaction type identification uses keywords: "Daily vault", "Weekly vault", "Security deposits"
- All three transactions share the same closing month in description
- Reference numbers are unique: `CLOSE-DAILY-*`, `CLOSE-WEEKLY-*`, `CLOSE-SECURITY-*`

## Future Enhancements

1. Add ability to view security deposit details in history
2. Add confirmation showing security amounts before reset
3. Add audit log for security resets
4. Add ability to exclude certain securities from reset
5. Add report showing security reset history over time
