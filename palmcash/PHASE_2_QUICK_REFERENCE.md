# Phase 2: Expense Management - Quick Reference

## Quick Start

### For Branch Managers

1. **Access Expense Management**
   - Dashboard → Click "Manage Expenses" button
   - Or go to: `/dashboard/expenses/`

2. **Add New Expense**
   - Click "Add Expense" button
   - Fill form:
     - Amount (K) - required
     - Expense Category - required (5 options)
     - Date - required
     - Description - optional
   - Click "Save Expense"

3. **View Expenses**
   - See all expenses for your branch
   - Filter by date range
   - Filter by category
   - View summary totals

4. **Generate Report**
   - Click "View Report" link
   - Optionally filter by date range
   - See breakdown by category
   - View percentages and totals
   - Print if needed

---

## Expense Categories

| Code | Category | Description |
|------|----------|-------------|
| EXP-001 | Cleaning costs | Cleaning supplies and services |
| EXP-002 | Stationery | Office supplies |
| EXP-003 | Rentals | Office rent and equipment |
| EXP-004 | Talk time | Mobile airtime and communication |
| EXP-005 | Transport | Transportation and fuel |

---

## URL Routes

| Route | Purpose |
|-------|---------|
| `/dashboard/expenses/` | View all expenses |
| `/dashboard/expenses/create/` | Add new expense |
| `/dashboard/expenses/report/` | View expense report |

---

## Key Features

### Expense List
- ✅ View all branch expenses
- ✅ Filter by date range
- ✅ Filter by category
- ✅ Pagination (50 per page)
- ✅ Summary totals

### Expense Form
- ✅ Simple form with 3 required fields
- ✅ Dropdown for predefined categories
- ✅ Optional description
- ✅ Automatic branch assignment

### Expense Report
- ✅ Aggregation by category
- ✅ Show count and total per category
- ✅ Calculate percentages
- ✅ Visual progress bars
- ✅ Print functionality

---

## Database Models

### ExpenseCode
- Predefined categories
- 5 codes created
- Cannot be modified by managers

### Expense
- Main expense tracking
- Fields: amount, code, date, description, branch, manager
- Linked to ExpenseCode

### ExpenseApprovalLog
- Audit trail for approvals
- Tracks all approval actions

---

## Views

### expense_list()
- Display expenses for manager's branch
- Filter by date and category
- Pagination support
- Summary cards

### expense_create()
- Form to enter new expense
- Validate required fields
- Automatic branch/user assignment
- Redirect to list on success

### expense_report()
- Generate report by category
- Aggregate totals and percentages
- Support date range filtering
- Visual display with progress bars

---

## Templates

### expense_list.html
- List view with filtering
- Summary cards
- Pagination
- Quick action buttons

### expense_form.html
- Entry form
- Required field validation
- Optional description
- Branch display

### expense_report.html
- Report view
- Category breakdown
- Visual charts
- Print button
- Summary statistics

---

## Security

- ✅ Role-based access (manager only)
- ✅ Branch-scoped data
- ✅ User assignment automatic
- ✅ All actions logged
- ✅ Predefined categories (no modification)

---

## Compliance

All 8 acceptance criteria for Requirement 2.2 are met:

1. ✅ Form to enter expenses
2. ✅ Required fields: amount, code, date, optional description
3. ✅ Predefined categories available
4. ✅ Expense saved with branch and manager info
5. ✅ View expenses with date filtering
6. ✅ Filter by category
7. ✅ Generate report by category
8. ✅ Report shows: category, count, total, percentage

---

## Testing Checklist

- [ ] Can access expense management from dashboard
- [ ] Can view all expenses for branch
- [ ] Can filter by date range
- [ ] Can filter by category
- [ ] Can add new expense
- [ ] Can generate report
- [ ] Report shows correct totals
- [ ] Report shows correct percentages
- [ ] Can print report
- [ ] Pagination works correctly
- [ ] Only manager can access
- [ ] Only sees own branch expenses

---

## Troubleshooting

### Expense codes not showing
- Run: `python manage.py setup_expense_codes`
- Check database for ExpenseCode records

### Can't access expense management
- Check user role (must be 'manager')
- Check branch assignment
- Check URL: `/dashboard/expenses/`

### Report not showing data
- Check date range
- Check if expenses exist for period
- Check category filter

---

## Next Phase

Phase 3 will add:
- Fund transfers between branches
- Bank deposits
- Fund history tracking
- Dashboard integration

Estimated: 5-6 days

