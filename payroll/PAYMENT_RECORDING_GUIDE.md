# Payroll Payment Recording Guide

## How Admins Record Employee Payments

### Step-by-Step Process

#### 1. Access Payroll Module
- Navigate to **Payroll** from the main menu (only visible to users with payroll access)
- You'll see the payroll dashboard with current month statistics

#### 2. View Payroll Periods
- Click on **"Periods"** or **"View All Periods"** from the dashboard
- You'll see a list of all payroll periods (monthly)
- Each period shows:
  - Month and Year
  - Total Expected amount
  - Total Paid amount
  - Outstanding balance
  - Status (Open/Processing/Closed)

#### 3. Select a Period
- Click **"View Details"** on the period you want to process
- You'll see all employee payment records for that month
- The page shows:
  - Summary cards (Total Expected, Total Paid, Outstanding, Progress %)
  - Status breakdown (Pending, Paid, Partial, Overdue)
  - List of all employees with their payment status

#### 4. Record Individual Payment
- Find the employee you want to pay
- Click **"Record Payment"** button in the Actions column
- You'll see a payment form with:
  - Employee information (ID, Name, Branch, Position)
  - Payment details (Expected, Already Paid, Outstanding, Due Date)
  - Payment form fields:
    - **Payment Amount**: Pre-filled with outstanding amount (can be adjusted for partial payments)
    - **Payment Date**: Defaults to today
    - **Payment Reference**: Transaction ID, check number, etc.
    - **Notes**: Any additional information

#### 5. Submit Payment
- Fill in the payment details
- Click **"Record Payment"** button
- The system will:
  - Update the payment record
  - Auto-calculate the new status (Paid/Partial/Pending/Overdue)
  - Update period totals
  - Log the action in audit trail
  - Show success message

#### 6. Payment Status Updates
The system automatically updates status based on:
- **Paid**: Amount paid >= Expected amount
- **Partial**: Amount paid > 0 but < Expected amount
- **Overdue**: Due date passed and not fully paid
- **Pending**: Not yet paid and not overdue

### Features

#### Search & Filter
- Search employees by name or ID
- Filter by payment status (Pending, Paid, Partial, Overdue)

#### Payment Tracking
- View payment history for each employee
- See who processed each payment
- Track payment references and dates

#### Audit Trail
- All payment actions are logged
- View audit logs from the Payroll menu
- Includes user, action, timestamp, and IP address

### Payment Methods Supported
- Bank Transfer
- Cash
- Mobile Money

### Bank Details Display
When recording payment, if the employee has bank details on file, they will be displayed for reference:
- Bank Name
- Account Number
- Preferred Payment Method

## Generating Monthly Payroll

To create a new payroll period with all employee records:

```bash
python manage.py generate_payroll --month 4 --year 2026
```

This will:
- Create a new PayrollPeriod for the specified month
- Generate PayrollRecord for each active employee
- Set expected amounts from employee monthly_salary
- Calculate due dates based on employee payment_day
- Set initial status as "pending"

## Quick Access URLs

- Dashboard: `/payroll/`
- Periods List: `/payroll/periods/`
- Period Detail: `/payroll/periods/<period_id>/`
- Record Payment: `/payroll/records/<record_id>/pay/`
- Payment History: `/payroll/payments/`
- Audit Logs: `/payroll/audit-logs/`

## Tips

1. **Partial Payments**: You can record multiple partial payments for an employee. The system tracks the total and updates status accordingly.

2. **Payment References**: Always include transaction references for bank transfers to maintain proper audit trail.

3. **Due Dates**: Payments are marked overdue automatically after the due date passes.

4. **Period Status**: 
   - Keep periods "Open" while processing payments
   - Change to "Processing" when reviewing
   - Mark as "Closed" when month is complete

5. **Bulk Processing**: For now, payments are recorded individually. Bulk payment processing is planned for Priority 2.
