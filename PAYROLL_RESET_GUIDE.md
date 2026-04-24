# Payroll Data Reset Guide

## Problem
After resetting the database, the payroll dashboard shows:
- "Total Employees: 0" and "No employees yet" ✓ (correct)
- "This Month Paid: K10,000.00" ✗ (stale data from old PayrollPeriod/PayrollRecord tables)

## Root Cause
When you reset the database, you likely only cleared the `User` and `Employee` tables, but the `PayrollPeriod`, `PayrollRecord`, and `PayrollPayment` tables still contain old payment data.

## Solution

### Step 1: Reset ALL Payroll Data
Run this command to clear all payroll-related tables:

```bash
python manage.py reset_payroll --confirm
```

This will delete:
- All employees
- All payroll periods
- All payroll records
- All salary records
- All payments
- All audit logs

### Step 2: Sync Employees from User Accounts
After resetting, sync your staff users (admins, managers, loan officers) as employees:

```bash
python manage.py sync_employees
```

This will:
- Create employee records for all active staff users
- Assign employee IDs (EMP0001, EMP0002, etc.)
- Set their position based on their role
- Link them to their branches (if applicable)

### Step 3: Set Employee Salaries
Go to the Payroll → Employees page and set monthly salaries for each employee.

### Step 4: Generate Payroll Period
Once salaries are set, generate the current month's payroll period:
- Go to Payroll Dashboard
- Click "Payroll Periods"
- Click "Generate New Period"
- Select the current month (April 2026)

## Expected Result
After following these steps:
- Total Employees: [number of staff users]
- Total Payroll: K[sum of all salaries]
- This Month Paid: K0.00 (fresh start)
- Pending Payments: [number of employees with salary set]

## Quick Commands Summary
```bash
# 1. Reset all payroll data
python manage.py reset_payroll --confirm

# 2. Sync employees from users
python manage.py sync_employees

# 3. (Optional) Grant payroll access to specific users
python manage.py grant_payroll_access <username>
```
