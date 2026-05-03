
Palm Cash
Dashboard
Loans
Clients
Payments
Securities
Reports
2

Elizabeth moyo
Processing Fees
Kuku

← Dashboard
This Month

K0.00

Total Verified

K73.00

Pending Verification

K0.00

Total Collected

K73.00

By Officer
Officer	#	Total	Verified	Pending
prudence mutale	1	K73.00	K73.00	K0.00
Pending Verification
1
Search & Filter
Search
App #, Borrower name...
Officer

All Officers
Group

All Groups
From

dd/mm/yyyy
To

dd/mm/yyyy
Search
Clear
All Fees
1 total
Date	App #	Borrower	Group	Officer	Fee	Status	Verified By	Action
03 May 2026	LA-578B0083	Grace Bwalya	
Dove	prudence mutale	K73.00	Verified	Elizabeth moyo
03 May 2026	—
Palm Cash
Professional Loan Management

Streamline your lending operations with our comprehensive loan management system. Trusted by financial institutions across the region.

Quick Links
Dashboard
Collections
Approvals
Support
Notifications
Help Center
Contact Us
© 2025 Palm Cash. All rights reserved.

Version 1.0 | Last Updated: January 6, 2026

Powered by Palm Cash Team# Scripts to Run - Expense Category Fixes

## Issue Summary
- **Problem 1**: Duplicate "Other" entries in ExpenseCode and ExpenseCategory tables
- **Problem 2**: Missing "Data Bundle" expense category

## Scripts to Run (in order)

### 1. Remove Duplicate "Other" Entries
```bash
python remove_duplicate_other.py
```

**What it does:**
- Finds all "Other" entries in ExpenseCode and ExpenseCategory
- Keeps the first one (lowest ID)
- Updates any expenses using duplicates to point to the kept entry
- Deletes the duplicate entries
- Shows before/after summary

**Expected output:**
```
======================================================================
REMOVING DUPLICATE 'OTHER' ENTRIES
======================================================================

1. Checking ExpenseCategory for duplicates...
----------------------------------------------------------------------
Found X 'Other' categories

Keeping: ID X - Other
Removing X duplicate(s):
  - ID X: Updating X expense(s) to use ID X
    ✓ Deleted duplicate ID X

✓ Removed X duplicate ExpenseCategory entries

2. Checking ExpenseCode for duplicates...
----------------------------------------------------------------------
Found X 'Other' expense codes

Keeping: ID X - CODE - Other
Removing X duplicate(s):
  - ID X (CODE): Updating X expense(s) to use ID X
    ✓ Deleted duplicate ID X

✓ Removed X duplicate ExpenseCode entries

======================================================================
FINAL STATE
======================================================================

Expense Categories:
  - Category Name (ID: X, Used by X expenses)
  ...

Expense Codes:
  - CODE: Name (ID: X, Used by X expenses)
  ...

======================================================================
✓ CLEANUP COMPLETE
======================================================================
```

### 2. Add Data Bundle Category
```bash
python add_data_bundle_category.py
```

**What it does:**
- Checks if "Data Bundle" category already exists
- Creates it if it doesn't exist
- Shows all active expense categories

**Expected output:**
```
✓ Created 'Data Bundle' category (ID: X)

All Expense Categories:
============================================================
  - Cleaning costs
  - Data Bundle
  - Other
  - Rentals
  - Stationery
  - Talk time
  - Transport

Total: 7 active categories
```

### 3. Restart the Server
```bash
sudo systemctl restart gunicorn
```

## Verification Steps

After running the scripts:

1. **Check the expense creation form:**
   - Go to: https://palmcashloans.site/dashboard/expenses/create/?branch=Kamwala%20south
   - The "Expense Category" dropdown should show:
     - Cleaning costs
     - Data Bundle ← NEW
     - Other ← Only ONE entry
     - Rentals
     - Stationery
     - Talk time
     - Transport

2. **Verify no duplicates:**
   - There should be only ONE "Other" option
   - All categories should appear only once

## Notes

- Both scripts are safe to run multiple times
- They check for existing data before making changes
- They preserve all expense records by updating references
- No data will be lost

## If You See Errors

If you see any errors, copy the full error message and share it so we can fix the issue.

---
**Status**: Ready to run
**Date**: May 2, 2026
