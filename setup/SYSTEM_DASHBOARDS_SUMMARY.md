# PalmCash System - Dashboard Summary

## Overview
PalmCash is a comprehensive loan management system designed for microfinance institutions. It provides role-based dashboards for different user types: System Administrators, Managers, and Loan Officers.

---

## 1. SYSTEM ADMINISTRATOR DASHBOARD

### Purpose
Complete system oversight, configuration, and reporting.

### Key Sections

#### A. System Statistics
- **Total Users**: Count of all system users by role
- **Total Loans**: Active, completed, defaulted, and pending loans
- **Total Borrowers**: Active and inactive borrower accounts
- **Total Disbursed**: Sum of all loan principal amounts
- **Total Collected**: Sum of all payments received
- **Outstanding Balance**: Total remaining loan balances

#### B. Financial Overview
- **Total Interest Income**: Sum of (total_amount - principal) for all completed loans
- **Total Expenses**: Sum of all approved expenses
- **Total Security Deposits**: Sum of all verified security deposits
- **Profit/Loss**: Interest income minus total expenses
- **Branch Balances**: Current cash balance for each branch

#### C. Loan Management
- **Pending Approvals**: Loans awaiting admin/manager review
- **Pending Disbursements**: Approved loans waiting for disbursement
- **Overdue Loans**: Loans with missed payments
- **Default Rate**: Percentage of defaulted loans
- **Collection Rate**: Percentage of collected vs. disbursed

#### D. Officer Performance
- **Officer Workload**: Group count for each loan officer
- **Officers Below Threshold**: Officers with < 15 active groups (highlighted in red)
- **Officer Capacity**: Percentage of groups managed vs. maximum
- **Top Performers**: Officers with highest collection rates
- **Problem Officers**: Officers with high default rates

#### E. Expense Tracking
- **Expenses by Category**: Breakdown of salaries, rent, utilities, marketing, etc.
- **Monthly Expenses**: Trend of expenses over time
- **Approved vs. Pending**: Count and amount of expenses awaiting approval
- **Budget vs. Actual**: Comparison to budgeted expenses

#### F. Vault & Branch Management
- **Central Vault Balance**: Total cash in central vault
- **Branch Balances**: Individual branch cash positions
- **Transaction History**: Recent deposits, withdrawals, transfers
- **Branch Transfers**: Inter-branch cash movements

#### G. Security Deposits
- **Total Deposits Collected**: Sum of all verified deposits
- **Pending Verifications**: Deposits awaiting admin verification
- **Deposits by Officer**: Breakdown by loan officer
- **Deposits by Branch**: Breakdown by branch location

#### H. Reports & Analytics
- **Daily Transaction Reports**: Aggregated transactions by date
- **Profit/Loss Dashboard**: Monthly, quarterly, YTD analysis
- **Expense Reports**: Category-based aggregation
- **Loan Collections View**: Portfolio analysis
- **Security Deposit Reports**: Separate tracking and verification status

---

## 2. MANAGER DASHBOARD

### Purpose
Operational oversight, expense management, and financial monitoring.

### Key Sections

#### A. Portfolio Overview
- **Total Active Loans**: Count of loans in active status
- **Total Disbursed (This Month)**: Sum of loans disbursed in current month
- **Total Collected (This Month)**: Sum of payments received in current month
- **Outstanding Balance**: Total remaining to be collected
- **Collection Rate**: Percentage of collected vs. disbursed

#### B. Loan Officer Performance
- **Officer List**: All loan officers with their metrics
- **Groups Managed**: Count of active groups per officer
- **Minimum Threshold Status**: 
  - ✅ Green: Officer has ≥15 groups (eligible to approve loans)
  - ⚠️ Yellow: Officer has 10-14 groups (approaching threshold)
  - ❌ Red: Officer has <10 groups (below threshold, cannot approve)
- **Collection Performance**: Percentage of loans collected per officer
- **Default Rate**: Percentage of defaulted loans per officer

#### C. Expense Management
- **Pending Expenses**: Expenses awaiting manager approval
- **Approved Expenses (This Month)**: Total approved expenses
- **Expenses by Category**: Breakdown of operational expenses
- **Monthly Expense Trend**: Chart showing expense patterns
- **Budget Status**: Comparison to allocated budget

#### D. Financial Summary
- **Interest Income (This Month)**: Interest earned from active loans
- **Total Expenses (This Month)**: All approved operational expenses
- **Profit/Loss (This Month)**: Interest income minus expenses
- **Profit/Loss (Previous Month)**: Comparison metric
- **Profit/Loss (YTD)**: Year-to-date performance

#### E. Vault & Branch Operations
- **Branch Balances**: Current cash position for each branch
- **Recent Transactions**: Last 10 vault transactions
- **Daily Inflows**: Total deposits and payments received
- **Daily Outflows**: Total disbursements and expenses
- **Net Daily Position**: Inflows minus outflows

#### F. Security Deposits
- **Total Deposits Collected**: Sum of verified deposits
- **Pending Verifications**: Deposits awaiting verification
- **Verification Status**: Count of verified vs. unverified
- **Deposits by Branch**: Breakdown by location

#### G. Daily Reports
- **Daily Transaction Report**: 
  - All transactions for selected date
  - Aggregated by type (disbursements, payments, deposits, expenses)
  - Total inflows and outflows
  - Net position for the day
- **Export Options**: PDF and CSV formats available

#### H. Alerts & Notifications
- **Overdue Loans**: Loans with missed payments
- **Officers Below Threshold**: Officers unable to approve loans
- **Pending Approvals**: Loans and expenses awaiting action
- **System Alerts**: Critical issues requiring attention

---

## 3. LOAN OFFICER DASHBOARD

### Purpose
Personal workload management, group oversight, and loan portfolio tracking.

### Key Sections

#### A. Personal Profile
- **Name & Role**: Loan Officer
- **Groups Managed**: Count of active groups assigned
- **Minimum Threshold**: 
  - ✅ Eligible to approve loans (≥15 groups)
  - ❌ Not eligible (< 15 groups)
- **Borrowers Managed**: Total borrowers across all groups
- **Active Loans**: Total active loans in portfolio

#### B. Group Management
- **My Groups**: List of all assigned groups
  - Group name
  - Branch location
  - Payment day
  - Number of members
  - Status (active/inactive)
- **Create New Group**: Form to create new borrower group
  - Required fields: name, branch, payment_day, max_members
  - Auto-assigns creating officer as manager

#### C. Loan Portfolio
- **Total Disbursed**: Sum of principal amounts for all loans
- **Total Collected**: Sum of all payments received
- **Outstanding Balance**: Total remaining to collect
- **Collection Rate**: Percentage of collected vs. disbursed
- **Overdue Loans**: Count and total amount of overdue loans

#### D. Collections View
- **Loans by Status**: 
  - Active: Loans currently being repaid
  - Completed: Fully repaid loans
  - Defaulted: Loans in default
- **Loan Details**:
  - Borrower name
  - Loan amount (principal)
  - Amount paid
  - Balance remaining
  - Next payment due date
  - Days overdue (if applicable)
- **Portfolio Totals**:
  - Total disbursed
  - Total collected
  - Total outstanding
  - Collection rate percentage

#### E. Borrower Management
- **My Borrowers**: List of all borrowers in assigned groups
  - Borrower name
  - Group assignment
  - Active loans count
  - Total borrowed
  - Total paid
- **Borrower Details**: Individual borrower profile with loan history

#### F. Loan Approval & Disbursement
- **Pending Approvals**: Loans awaiting officer approval
  - Borrower name
  - Loan amount
  - Purpose
  - Approval button (if eligible)
- **Approval Eligibility Check**:
  - ✅ Can approve if: ≥15 active groups
  - ❌ Cannot approve if: <15 active groups
  - Error message shows current group count and requirement
- **Pending Disbursements**: Approved loans awaiting disbursement
  - Security deposit status (required, paid, verified)
  - Disbursement button (only if deposit verified)

#### G. Security Deposit Tracking
- **Deposits Required**: Loans requiring 10% security deposit
- **Deposits Pending**: Deposits not yet paid
- **Deposits Paid**: Deposits paid but not verified
- **Deposits Verified**: Deposits verified and ready for disbursement
- **Record Deposit**: Form to record deposit payment
  - Amount
  - Payment date
  - Payment method (cash, bank transfer, mobile money, check)
  - Receipt number

#### H. Performance Metrics
- **Active Groups**: Count of groups managed
- **Active Borrowers**: Count of borrowers in groups
- **Active Loans**: Count of loans in portfolio
- **Collection Rate**: Percentage of collected vs. disbursed
- **Default Rate**: Percentage of defaulted loans
- **Average Loan Size**: Average principal amount

#### I. Notifications & Alerts
- **Pending Actions**: Loans awaiting approval/disbursement
- **Overdue Loans**: Loans with missed payments
- **Threshold Status**: Warning if below 15 groups
- **Deposit Reminders**: Deposits pending verification

---

## 4. SYSTEM-WIDE FEATURES

### A. User Management
- **Role-Based Access Control**:
  - Admin: Full system access
  - Manager: Operational oversight
  - Loan Officer: Personal workload
  - Borrower: Loan application and payment tracking
- **Permission System**:
  - `can_create_group`: Loan officers only
  - `can_approve_loans`: Loan officers with ≥15 groups
  - `can_disburse_loans`: Loan officers with verified deposits
  - `can_verify_deposits`: Admins and managers
  - `can_manage_expenses`: Managers and admins

### B. Loan Management
- **Loan Types**: Daily and weekly repayment frequencies
- **Loan Status**: Pending → Approved → Disbursed → Active → Completed/Defaulted
- **Loan Calculations**:
  - Total amount = Principal + (Principal × Interest Rate)
  - Payment amount = Total amount ÷ Term (days or weeks)
  - Security deposit = Principal × 10%
  - Balance remaining = Total amount - Amount paid

### C. Group Management
- **Group Fields**:
  - Name (unique)
  - Description
  - Branch location
  - Payment day (e.g., Monday, Tuesday)
  - Max members
  - Assigned officer
  - Status (active/inactive)
- **Group Filtering**: Officers see only their assigned groups

### D. Borrower Management
- **Borrower Fields**:
  - Full name
  - Phone number
  - Email
  - Address
  - Group assignment
  - Status (active/inactive)
- **Borrower Filtering**: Officers see only borrowers in their groups

### E. Expense Tracking
- **Expense Categories**:
  - Salaries
  - Rent
  - Utilities
  - Marketing
  - Transportation
  - Office Supplies
  - Other
- **Expense Fields**:
  - Category
  - Amount
  - Date
  - Description
  - Branch
  - Receipt (optional)
  - Approval status
- **Expense Workflow**: Created → Pending → Approved/Rejected

### F. Vault & Branch Transactions
- **Transaction Types**:
  - Deposit to vault
  - Withdrawal from vault
  - Branch transfer
  - Loan disbursement
  - Payment collection
- **Transaction Fields**:
  - Type
  - Amount
  - Source branch
  - Destination branch
  - Date/time
  - Reference number
  - Description
- **Balance Calculation**: Inflows - Outflows = Current balance

### G. Security Deposits
- **Deposit Workflow**:
  1. Loan approved → Deposit required (10% of principal)
  2. Borrower pays deposit → Recorded in system
  3. Manager verifies deposit → Marked as verified
  4. Loan can be disbursed → Only if verified
- **Deposit Tracking**:
  - Required amount
  - Paid amount
  - Payment date
  - Payment method
  - Verification status
  - Verified by (admin/manager)
  - Verification date

### H. Reporting & Analytics
- **Daily Transaction Reports**:
  - Date-based aggregation
  - Transaction types: disbursements, payments, deposits, expenses
  - Totals: inflows, outflows, net
  - Export: PDF, CSV
- **Profit/Loss Dashboard**:
  - Interest income calculation
  - Expense aggregation
  - Profit/loss by period (month, quarter, YTD)
  - Filtering: date range, branch, officer
- **Expense Reports**:
  - Aggregation by category
  - Aggregation by time period
  - Filtering options
  - Export functionality
- **Loan Collections View**:
  - Officer portfolio analysis
  - Loan status breakdown
  - Portfolio totals
  - Overdue highlighting
  - Filtering: group, status, overdue

### I. Notifications & Alerts
- **Email Notifications**:
  - Loan application submitted
  - Loan approved/rejected
  - Loan disbursed
  - Payment received
  - Overdue payment reminder
  - Deposit verification pending
- **In-App Notifications**:
  - Real-time alerts
  - Action items
  - System messages
  - Approval requests

### J. Data Validation & Security
- **Field Validation**:
  - Required fields enforcement
  - Amount validation (positive values)
  - Date validation
  - Unique constraints (group names, application numbers)
- **Permission Checks**:
  - Row-level permissions (officers see only their data)
  - Role-based access control
  - Action authorization (approve, disburse, verify)
- **Audit Trail**:
  - User tracking (created_by, updated_by)
  - Timestamp tracking (created_at, updated_at)
  - Action logging

---

## 5. KEY BUSINESS RULES

### Loan Officer Requirements
- **Minimum Groups**: Must manage ≥15 active groups to approve loans
- **Group Assignment**: Auto-assigned as manager when creating group
- **Loan Approval**: Can only approve loans for borrowers in their groups
- **Loan Disbursement**: Can only disburse if security deposit is verified

### Security Deposit Rules
- **Calculation**: Always 10% of principal amount
- **Timing**: Required before loan disbursement
- **Verification**: Must be verified by admin/manager before disbursement
- **Tracking**: Stored separately from regular payments

### Expense Rules
- **Approval**: All expenses require manager/admin approval
- **Categories**: Must be assigned to predefined categories
- **Documentation**: Receipt optional but recommended
- **Reporting**: Separate from loan payments in financial reports

### Branch Balance Rules
- **Calculation**: Sum of inflows minus sum of outflows
- **Inflows**: Deposits, payments, transfers in
- **Outflows**: Withdrawals, disbursements, transfers out
- **Tracking**: Running balance maintained for each branch

---

## 6. SYSTEM WORKFLOW EXAMPLES

### Example 1: Loan Officer Approving a Loan
1. Borrower applies for loan
2. Loan officer reviews application
3. **Check**: Officer has ≥15 active groups? ✅ Yes
4. Officer approves loan
5. System creates security deposit record (10% of principal)
6. Borrower pays security deposit
7. Loan officer records deposit payment
8. Manager verifies deposit
9. Loan officer disburses loan
10. System generates payment schedule
11. Borrower begins repayment

### Example 2: Manager Reviewing Financial Performance
1. Manager accesses dashboard
2. Views profit/loss for current month
3. Sees interest income: K50,000
4. Sees total expenses: K15,000
5. Calculates profit: K35,000
6. Compares to previous month: K32,000 (↑ 9% improvement)
7. Filters by branch to see performance by location
8. Identifies top-performing branch
9. Exports report for board meeting

### Example 3: Admin Monitoring Officer Workload
1. Admin views officer workload dashboard
2. Sees all officers with group counts
3. Identifies 3 officers below 15-group threshold
4. Marks them in red for attention
5. Assigns additional groups to bring them above threshold
6. Verifies they can now approve loans
7. Sends notification to officers about new assignments

---

## 7. SUMMARY TABLE

| Feature | Admin | Manager | Loan Officer | Borrower |
|---------|-------|---------|--------------|----------|
| View all loans | ✅ | ✅ | Own only | Own only |
| Approve loans | ✅ | ✅ | If ≥15 groups | ❌ |
| Disburse loans | ✅ | ✅ | If deposit verified | ❌ |
| Create groups | ✅ | ✅ | ✅ | ❌ |
| Manage expenses | ✅ | ✅ | ❌ | ❌ |
| Verify deposits | ✅ | ✅ | ❌ | ❌ |
| View reports | ✅ | ✅ | Own portfolio | Own loans |
| Manage users | ✅ | ❌ | ❌ | ❌ |
| View vault | ✅ | ✅ | ❌ | ❌ |
| Record deposits | ✅ | ✅ | ✅ | ✅ |

---

## 8. TECHNICAL IMPLEMENTATION

### Models
- **User**: Extended Django user with role field
- **BorrowerGroup**: Groups with branch and payment_day
- **Borrower**: Individual borrowers in groups
- **Loan**: Loan applications with daily/weekly repayment
- **Payment**: Individual payment records
- **SecurityDeposit**: 10% deposit tracking
- **Expense**: Operational expenses with categories
- **VaultTransaction**: Cash movements between branches
- **OfficerAssignment**: Officer workload tracking

### Views
- **Admin Dashboard**: System statistics and reporting
- **Manager Dashboard**: Operational oversight
- **Loan Officer Dashboard**: Personal workload
- **Borrower Dashboard**: Loan tracking
- **Reporting Views**: Daily reports, P&L, collections

### Permissions
- `can_create_group`: Loan officers
- `can_approve_loans`: Loan officers with ≥15 groups
- `can_disburse_loans`: Loan officers with verified deposits
- `can_verify_deposits`: Admins and managers
- `can_manage_expenses`: Managers and admins

---

## Conclusion

PalmCash provides a comprehensive, role-based loan management system with:
- **Clear role separation** for admins, managers, and loan officers
- **Automated validations** for loan approval and disbursement
- **Comprehensive reporting** for financial analysis
- **Security deposit enforcement** before disbursement
- **Expense tracking** separate from loan payments
- **Branch-level cash management** with vault transactions
- **Performance metrics** for officer workload monitoring

The system ensures compliance with business rules while providing intuitive dashboards for each user role.
