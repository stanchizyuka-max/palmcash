# Expense Codes System Documentation

## Overview
The Palm Cash application uses an expense categorization system based on predefined expense codes. These codes help managers track and report on different types of branch expenses.

## Predefined Expense Codes

| Code | Name | Description |
|------|------|-------------|
| EXP-001 | Cleaning costs | Cleaning supplies and services for branch office |
| EXP-002 | Stationery | Office stationery and supplies |
| EXP-003 | Rentals | Office rent and equipment rentals |
| EXP-004 | Talk time | Mobile phone airtime and communication costs |
| EXP-005 | Transport | Transportation and fuel costs |

## Database Models

### ExpenseCode Model
Located in: `expenses/models.py`

```python
class ExpenseCode(models.Model):
    code = models.CharField(max_length=20, unique=True)  # e.g., "EXP-001"
    name = models.CharField(max_length=100)  # e.g., "Cleaning costs"
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Expense Model
Located in: `expenses/models.py`

```python
class Expense(models.Model):
    expense_code = models.ForeignKey(ExpenseCode, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    branch = models.CharField(max_length=100)
    expense_date = models.DateField()
    description = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

## Manager Dashboard Features

### 1. Add Expense
**URL**: `/dashboard/expense/create/`
**View**: `dashboard/views.py::expense_create()`

Managers can add new expenses by:
1. Selecting an expense code from the dropdown
2. Entering the amount
3. Selecting the date
4. Adding optional description

### 2. View Expenses
**URL**: `/dashboard/expenses/`
**View**: `dashboard/views.py::expense_list()`

Managers can:
- View all expenses for their branch
- Filter by date range
- Filter by expense code
- See total expenses

### 3. Expense Report
**URL**: `/dashboard/expense-report/`
**View**: `dashboard/views.py::expense_report()`

Managers can:
- Generate reports by expense code
- Filter by date range
- See breakdown of expenses by category
- View percentage distribution

## Adding New Expense Codes

### Method 1: Django Admin
1. Log in as admin
2. Go to Django Admin
3. Navigate to Expenses → Expense Codes
4. Click "Add Expense Code"
5. Fill in code, name, description
6. Set is_active to True
7. Save

### Method 2: Management Command
```bash
python manage.py setup_expense_codes
```

### Method 3: Django Shell
```python
from expenses.models import ExpenseCode

ExpenseCode.objects.create(
    code='EXP-006',
    name='New Category',
    description='Description here',
    is_active=True
)
```

## Deactivating Expense Codes

To deactivate an expense code (without deleting it):
```python
code = ExpenseCode.objects.get(code='EXP-001')
code.is_active = False
code.save()
```

The code will no longer appear in dropdowns but existing expenses will retain the reference.

## Querying Expense Data

### Get all active expense codes
```python
from expenses.models import ExpenseCode
codes = ExpenseCode.objects.filter(is_active=True)
```

### Get expenses by code
```python
from expenses.models import Expense, ExpenseCode
code = ExpenseCode.objects.get(code='EXP-001')
expenses = Expense.objects.filter(expense_code=code)
```

### Get total expenses by code
```python
from django.db.models import Sum
from expenses.models import Expense, ExpenseCode

code = ExpenseCode.objects.get(code='EXP-001')
total = Expense.objects.filter(expense_code=code).aggregate(Sum('amount'))['amount__sum']
```

### Get expenses for a specific branch
```python
from expenses.models import Expense
branch_expenses = Expense.objects.filter(branch='Main Branch')
```

## Related Files

- **Models**: `palmcash/palmcash/expenses/models.py`
- **Views**: `palmcash/palmcash/dashboard/views.py`
- **Templates**: 
  - `palmcash/palmcash/dashboard/templates/dashboard/expense_form.html`
  - `palmcash/palmcash/dashboard/templates/dashboard/expense_list.html`
  - `palmcash/palmcash/dashboard/templates/dashboard/expense_report.html`
- **Migrations**: `palmcash/palmcash/expenses/migrations/`
- **Management Commands**: `palmcash/palmcash/expenses/management/commands/setup_expense_codes.py`

## Troubleshooting

### Dropdown shows no options
**Cause**: ExpenseCode table is empty
**Solution**: Run `python manage.py migrate` or `python manage.py setup_expense_codes`

### Can't create expense with selected code
**Cause**: Selected code is inactive or doesn't exist
**Solution**: Verify the code is active in the database

### Report shows no data
**Cause**: No expenses recorded for the selected date range
**Solution**: Check date filters and ensure expenses exist in the database

## Future Enhancements

Potential improvements to the expense system:
1. Add expense approval workflow
2. Add budget limits per code
3. Add recurring expenses
4. Add expense attachments/receipts
5. Add expense reconciliation
6. Add multi-level categorization
7. Add expense forecasting
