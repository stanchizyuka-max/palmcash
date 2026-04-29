# Dashboard Collections Calculation Fix

## Issue Identified
The dashboard "Today's Collections" had multiple calculation issues:
1. It was using a date range filter instead of filtering for just today's date
2. Initial fix excluded completed loans entirely, which hid collections made today that completed loans

### Symptoms
- **Initial Problem**: Expected K276, Collected K5,492 (1988% rate) - showing month-to-date
- **After First Fix**: Expected K0, Collected K0 - but this hid K5,492 collected today that completed loans
- **Correct Behavior**: Expected K0 (no active loans), Collected K5,492 (today's collections including loan completions)

### Root Cause
The dashboard needed different logic for "Expected" vs "Collected":
- **Expected**: Should only count active loans (loans still needing payment)
- **Collected**: Should count ALL collections made today (including those that completed loans)

## Final Fix Applied

### Loan Officer Dashboard (Line 158-177)
```python
# Today's collections - use actual today, not date range filter
from datetime import date
today = date.today()

# For EXPECTED: Only count active loans (loans that still need payment)
today_collections_active = PaymentCollection.objects.filter(
    related_query,
    collection_date=today,
    loan__status='active'
).distinct()

# For COLLECTED: Count both active loans AND loans completed today
# (to show today's collections even if they completed the loan)
today_collections_all = PaymentCollection.objects.filter(
    related_query,
    collection_date=today
).distinct()

today_expected = sum(c.expected_amount for c in today_collections_active) or 0
today_collected = sum(c.collected_amount for c in today_collections_all) or 0
today_pending = max(0, today_expected - today_collected)
```

### Manager Dashboard (Line 1158-1177)
Applied the same logic - separate queries for expected (active only) vs collected (all).

### Clients Expected to Pay Today
Updated to use `today_collections_active` so it only shows clients with active loans, not completed ones.

## Expected Results After Fix

### When All Loans Are Completed (but collections made today):
- **Expected**: K0 (no active loans = no expected payments)
- **Collected**: K5,492 (shows today's collections that completed the loans)
- **Clients Expected to Pay Today**: Empty list (no active loans)
- **Collection Rate**: N/A or 100% (collected more than expected)

### When There Are Active Loans:
- **Expected**: Shows only expected payments from active loans for today
- **Collected**: Shows all collections from today (active + completed)
- **Collection Rate**: Realistic percentage (0-100%+)
- **Clients Expected to Pay Today**: Shows only clients with active loans

## Key Insight
The fix recognizes that:
- **"Expected"** is forward-looking: What do we expect to collect from active loans?
- **"Collected"** is backward-looking: What did we actually collect today (regardless of loan status)?

This allows the dashboard to show K0 expected (correct - no active loans) while still showing K5,492 collected (correct - today's work completed 2 loans).

## Verification Status
✅ **Loan Officer Dashboard**: Fixed - separate queries for expected vs collected
✅ **Manager Dashboard**: Fixed - separate queries for expected vs collected
✅ **Admin Dashboard**: N/A - doesn't have today's collections

## Files Modified
- `dashboard/views.py` (Lines 158-177, 1158-1177, 224)

## Date: April 29, 2026
