# Dashboard Collections Calculation Fix

## Issue Identified
The dashboard "Today's Collections" was showing incorrect values for two reasons:
1. It was using a date range filter instead of filtering for just today's date
2. It was including collections from **completed loans** instead of only **active loans**

### Symptoms
- **Manager Dashboard**: Expected K276, Collected K5,492 (1988% collection rate - impossible!)
- **Officer Dashboard**: Expected K829, Collected K8,708
- The "Today's Collections" was showing month-to-date collections
- **Clients Expected to Pay Today** was showing clients whose loans were already completed
- Expected amount showed K276 even when all loans were completed (should be K0)

### Root Cause
In `dashboard/views.py`, the loan officer dashboard had two issues:

**Issue 1:** Using date range instead of exact date
```python
today_collections = PaymentCollection.objects.filter(
    related_query,
    collection_date__range=[date_from_obj, date_to_obj]  # WRONG - uses date range
).distinct()
```

**Issue 2:** Not filtering out completed loans
```python
today_collections = PaymentCollection.objects.filter(
    related_query,
    collection_date=today  # Correct date, but missing loan status filter
).distinct()
```

This caused the dashboard to show collections from completed loans, making it appear that clients still had payments due today even after their loans were fully paid.

## Fix Applied

### Loan Officer Dashboard (Line 158-165)
Changed from:
```python
today_collections = PaymentCollection.objects.filter(
    related_query,
    collection_date__range=[date_from_obj, date_to_obj]
).distinct()
```

To:
```python
# Today's collections - use actual today, not date range filter
# Only show collections from ACTIVE loans (exclude completed loans)
from datetime import date
today = date.today()
today_collections = PaymentCollection.objects.filter(
    related_query,
    collection_date=today,  # Changed from date range to just today
    loan__status='active'  # Only show collections from active loans
).distinct()
```

### Manager Dashboard (Line 1150-1156)
Changed from:
```python
today_collections = PaymentCollection.objects.filter(
    loan__loan_officer__officer_assignment__branch=branch.name,
    collection_date=today
).distinct()
```

To:
```python
# Today's collections - only include loans where officer is from this branch
# Only show collections from ACTIVE loans (exclude completed loans)
today = date.today()
today_collections = PaymentCollection.objects.filter(
    loan__loan_officer__officer_assignment__branch=branch.name,
    collection_date=today,
    loan__status='active'  # Only show collections from active loans
).distinct()
```

### Admin Dashboard
Does not have a "Today's Collections" section - only shows total repaid across all time.

## Expected Results After Fix

### When All Loans Are Completed:
- **Expected**: K0 (no active loans = no expected payments)
- **Collected**: K0 (no collections from active loans today)
- **Clients Expected to Pay Today**: Empty list (no active loans)

### When There Are Active Loans:
- **Expected**: Shows only expected payments from active loans for today
- **Collected**: Shows only collections from active loans for today
- **Collection Rate**: Realistic percentage (0-100%)
- **Clients Expected to Pay Today**: Shows only clients with active loans

## Verification Status
✅ **Loan Officer Dashboard**: Fixed - now uses `collection_date=today` AND `loan__status='active'`
✅ **Manager Dashboard**: Fixed - now uses `collection_date=today` AND `loan__status='active'`
✅ **Admin Dashboard**: N/A - doesn't have today's collections

## Testing Required
Once the MySQL database server is running, test:
1. Login as a loan officer with all completed loans - should show K0 expected, K0 collected
2. Login as a loan officer with active loans - should show realistic amounts
3. Login as a manager and verify same behavior
4. Verify "Clients Expected to Pay Today" only shows clients with active loans

## Files Modified
- `dashboard/views.py` (Lines 158-165, 1150-1156)

## Date: April 29, 2026
