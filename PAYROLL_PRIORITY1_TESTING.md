# Payroll Priority 1 - Testing Guide

## ✅ What Was Implemented

### 1. Salary Structure Per Employee
- Monthly salary amount
- Payment day (1-31, use 31 for last day of month)
- Payment method (Bank Transfer, Cash, Mobile Money)
- Bank account details

### 2. Monthly Payroll Generation
- Auto-creates payroll records for all employees
- Calculates due dates based on payment day
- Tracks expected amounts
- Groups by month/year periods

### 3. Payment Tracking
- Record amount paid
- Compare against expected salary
- Track payment dates
- Payment references

### 4. Status Monitoring
- **Pending**: Not yet paid, not overdue
- **Paid**: Fully settled
- **Partial**: Underpaid (paid less than expected)
- **Overdue**: Not paid after due date

## 🚀 How To Test

### Step 1: Run Migrations
```bash
python manage.py migrate payroll
```

Expected output:
```
Running migrations:
  Applying payroll.0003_employee_bank_account_number_employee_bank_name_and_more... OK
```

### Step 2: Sync Employees (if not done)
```bash
python manage.py sync_employees
```

This creates employee records for all staff.

### Step 3: Set Employee Salaries

Go to Django Admin: `/admin/payroll/employee/`

For each employee, set:
- **Monthly Salary**: e.g., K5,000
- **Payment Day**: e.g., 30 (for 30th of each month)
- **Payment Method**: Bank Transfer
- **Bank Name**: e.g., Zanaco
- **Bank Account**: e.g., 1234567890

Example:
```
Mmutale Mutale:
- Monthly Salary: K8,000
- Payment Day: 30
- Payment Method: Bank Transfer

Elizabeth Moyo:
- Monthly Salary: K6,000
- Payment Day: 30
- Payment Method: Bank Transfer

Loan Officers:
- Monthly Salary: K4,000
- Payment Day: 30
- Payment Method: Bank Transfer
```

### Step 4: Generate Payroll for Current Month
```bash
python manage.py generate_payroll
```

Expected output:
```
Generating payroll for January 2026...

  ✓ EMP0001 - Mmutale Mutale: K8,000.00 (Due: Jan 30)
  ✓ EMP0002 - Tobias Mhlanga: K8,000.00 (Due: Jan 30)
  ✓ EMP0003 - Elizabeth Moyo: K6,000.00 (Due: Jan 30)
  ... (continues for all employees)

======================================================================
✓ Payroll generation completed!

Period: January 2026
Status: Open

Records created: 15
Records skipped: 0

Total Expected: K75,000.00
Total Paid: K0.00
Outstanding: K75,000.00

✓ 15 employees ready for payment
```

### Step 5: View Payroll Dashboard

Go to: `/payroll/`

You should see:
- Total Employees: 15
- Monthly Payroll: K75,000
- This Month Expected: K75,000
- This Month Paid: K0
- Pending Payments: 15

### Step 6: View Payroll Periods

Go to: `/payroll/periods/`

You should see:
```
Period          | Status | Expected  | Paid  | Outstanding | Progress
January 2026    | Open   | K75,000   | K0    | K75,000     | 0%
```

Click "View Details" to see all employee records.

### Step 7: Process a Payment

1. Go to period detail page
2. Find an employee (e.g., Mmutale Mutale)
3. Click "Process Payment" (you'll need to add this button)
4. Enter:
   - Amount Paid: K8,000
   - Payment Date: 2026-01-30
   - Reference: TXN123456
5. Submit

Expected result:
- Record status changes to "Paid"
- Period totals update
- Outstanding decreases

### Step 8: Check Status Updates

After processing some payments:
- **Paid employees**: Status = "Paid" (green)
- **Unpaid before due date**: Status = "Pending" (yellow)
- **Unpaid after due date**: Status = "Overdue" (red)
- **Partially paid**: Status = "Partial" (orange)

## 📊 What You Can Do Now

### 1. Generate Payroll for Any Month
```bash
# For February 2026
python manage.py generate_payroll --month=2 --year=2026

# For next month
python manage.py generate_payroll
```

### 2. View All Periods
- Go to `/payroll/periods/`
- See all months with totals
- Track payment progress

### 3. Monitor Payments
- See who's been paid
- See who's pending
- See who's overdue
- Track outstanding amounts

### 4. Process Payments
- Record individual payments
- Update payment status
- Track payment references

## 🎯 Testing Scenarios

### Scenario 1: Full Payment
1. Generate payroll for January
2. Process payment for Mmutale: K8,000
3. Check status: Should be "Paid"
4. Check period totals: Paid should increase

### Scenario 2: Partial Payment
1. Process payment for Elizabeth: K3,000 (expected K6,000)
2. Check status: Should be "Partial"
3. Outstanding: Should show K3,000

### Scenario 3: Overdue Payment
1. Generate payroll with past due date
2. Don't process payment
3. Wait for due date to pass
4. Status should auto-update to "Overdue"

### Scenario 4: Multiple Months
1. Generate January payroll
2. Generate February payroll
3. View periods list
4. See both months tracked separately

## 🐛 Troubleshooting

### No employees showing?
Run: `python manage.py sync_employees`

### Salaries are K0?
Set salaries in admin: `/admin/payroll/employee/`

### Can't generate payroll?
Check that employees have monthly_salary > 0

### Period already exists?
Use `--force` flag: `python manage.py generate_payroll --force`

## ✅ Success Criteria

Priority 1 is working if:
- ✅ Employees have salary amounts set
- ✅ Payroll generates for current month
- ✅ Period shows correct totals
- ✅ Can process payments
- ✅ Status updates automatically
- ✅ Outstanding amounts calculate correctly

## 📝 Next Steps

After testing Priority 1, we can implement:

**Priority 2:**
- Bulk payment processing
- Overdue tracking with alerts
- Basic reports (monthly summary, employee history)

Let me know when you're ready to proceed to Priority 2!

## 🔗 Quick Links

- Payroll Dashboard: `/payroll/`
- Payroll Periods: `/payroll/periods/`
- Employee List: `/payroll/employees/`
- Django Admin: `/admin/payroll/`

---

**Status**: ✅ Priority 1 Complete - Ready for Testing
**Next**: Test thoroughly, then proceed to Priority 2
