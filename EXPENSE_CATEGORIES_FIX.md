# Expense Categories Dropdown Fix

## Problem
The expense categories dropdown menu was not showing on the manager dashboard when trying to add or filter expenses. The dropdown appeared empty even though the form was rendering correctly.

## Root Cause
The `ExpenseCode` table in the database was empty. The application uses `ExpenseCode` model to store predefined expense categories, but these records were never created in the database.

The system has two related models:
- **ExpenseCode**: Predefined expense categories (Cleaning costs, Stationery, Rentals, Talk time, Transport)
- **ExpenseCategory**: Alternative categorization model (currently not used in the manager dashboard)

## Solution
A data migration has been created to automatically populate the `ExpenseCode` table with the five predefined expense categories when migrations are run.

### File Created
- `palmcash/palmcash/expenses/migrations/0004_populate_expense_codes.py`

This migration:
1. Creates 5 predefined expense codes:
   - EXP-001: Cleaning costs
   - EXP-002: Stationery
   - EXP-003: Rentals
   - EXP-004: Talk time
   - EXP-005: Transport

2. Sets all codes as active (`is_active=True`)
3. Can be reversed if needed

## How to Apply the Fix

### Option 1: Run Migrations (Recommended)
```bash
cd palmcash/palmcash
python manage.py migrate
```

This will automatically run the new migration and populate the expense codes.

### Option 2: Run Management Command (Alternative)
If you prefer to use the existing management command:
```bash
cd palmcash/palmcash
python manage.py setup_expense_codes
```

## Verification
After applying the fix, the expense categories dropdown should show:
- Cleaning costs
- Stationery
- Rentals
- Talk time
- Transport

You can verify this by:
1. Logging in as a manager
2. Going to Dashboard → Add Expense
3. The "Expense Category" dropdown should now display all 5 categories

## Files Affected
- `palmcash/palmcash/expenses/migrations/0004_populate_expense_codes.py` (NEW)
- `palmcash/palmcash/expenses/models.py` (No changes needed)
- `palmcash/palmcash/dashboard/views.py` (No changes needed)
- `palmcash/palmcash/dashboard/templates/dashboard/expense_form.html` (No changes needed)

## Related Code
The following views use the expense codes:
- `dashboard/views.py::expense_create()` - Creates new expenses with selected code
- `dashboard/views.py::expense_list()` - Filters expenses by code
- `dashboard/views.py::expense_report()` - Generates reports by code

All these views query `ExpenseCode.objects.filter(is_active=True)` to populate the dropdown.
