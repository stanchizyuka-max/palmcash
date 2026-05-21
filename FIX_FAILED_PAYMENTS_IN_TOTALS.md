# Fix Failed Payments Included in Totals

## Problem
Failed/rejected payments were being included in payment totals and counts in the hierarchical payment views.

**Example:**
- ruth chisi had 2 payments:
  - PAY-000129: K210 (Pending) ✓
  - PAY-000107: K50 (Failed) ✗
- TOTAL showed: K260 (incorrect - includes failed payment)
- Should show: K210 (only pending/completed payments)

## Root Cause
The `_get_base_payment_queryset()` function in `payments/views_hierarchical.py` was not filtering out failed or cancelled payments. It was including ALL payments regardless of status.

## Fix Applied
Modified `_get_base_payment_queryset()` to exclude failed and cancelled payments:

```python
def _get_base_payment_queryset(user):
    """Get base payment queryset based on user role - excludes failed/cancelled payments"""
    qs = Payment.objects.select_related(
        'loan', 'loan__borrower', 'loan__loan_officer', 'loan__loan_officer__officer_assignment'
    ).exclude(status__in=['failed', 'cancelled'])
```

## What This Fixes

**Before:**
- All payments counted in totals (pending, completed, failed, cancelled)
- Failed payment K50 + Pending payment K210 = K260 total ✗

**After:**
- Only valid payments counted (pending, completed)
- Pending payment K210 = K210 total ✓
- Failed payments excluded from all views and totals

## Affected Views
This fix applies to all hierarchical payment views:
1. **Branch level** - Total payments per branch
2. **Officer level** - Total payments per officer
3. **Group level** - Total payments per group
4. **Client level** - Total payments per client (this is where you saw the issue)

## Deployment
```bash
cd ~/www/palmcashloans.site
git pull origin main
find . -name "*.pyc" -delete
sudo systemctl restart gunicorn
```

After deployment, ruth chisi's payment total will show K210 instead of K260.

## Related Fixes
This is part of a series of payment rejection fixes:
1. ✅ Payment rejection now reverts schedules and loan balance
2. ✅ Failed payments excluded from totals and counts
3. ✅ Payment PAY-000107 schedule reverted to unpaid
