# Security Withdrawals - How They Work

## Overview

Security withdrawals allow borrowers to withdraw part of their security deposit **after their loan is completed**. This gives clients flexibility to:
- Withdraw some cash (e.g., K300)
- Use the remaining security for a new loan via carry forward (e.g., K300)

## Process Flow

### 1. **Initiation (Loan Officer)**

**Location**: `loans/security_views.py` → `security_action()` view

**URL**: `/loans/<loan_id>/security/withdrawal/`

**Who Can Initiate**: Loan Officers, Managers, Admins

**Prerequisites**:
- Loan must be **completed** (not active)
- Security deposit must have available balance

**Steps**:
1. Officer navigates to completed loan detail page
2. Clicks "Withdrawal" action
3. Enters withdrawal amount (client's choice)
4. Adds optional notes
5. Submits request

### 2. **Validation (System)**

**Location**: `loans/security_services.py` → `initiate_security_withdrawal()`

**Checks Performed**:

```python
# 1. Loan must be completed
if loan.status != 'completed':
    return error

# 2. Security deposit must exist
deposit = loan.security_deposit

# 3. Amount must be positive
if amount <= 0:
    return error

# 4. Amount cannot exceed available security
if amount > deposit.available_security:
    return error

# NO minimum requirement - client can withdraw any amount
# Remaining security can be used for new loan
```

**Example**:
- Available security: K600
- Client wants to withdraw: K300
- Remaining for new loan: K300 ✅ Allowed

### 3. **Approval (Manager)**

**Location**: `loans/security_services.py` → `approve_security_transaction()`

**Who Can Approve**: Managers, Admins

**What Happens on Approval**:

```python
# 1. Update security deposit record
deposit.security_returned += withdrawal_amount
deposit.save()

# 2. Record vault transaction (money OUT)
vault.balance -= withdrawal_amount
vault.save()

# 3. Create vault transaction record
VaultTransaction.create(
    transaction_type='security_return',
    direction='out',
    amount=withdrawal_amount,
    description='Security return for [loan_number]'
)

# 4. Update transaction status
txn.status = 'approved'
txn.approved_by = manager
txn.save()
```

## Key Differences: Withdrawal vs Return vs Adjustment

### Security Withdrawal
- **When**: After loan completion
- **Purpose**: Client wants partial cash, rest for new loan
- **Constraint**: None - client decides the split
- **Example**: K600 available → withdraw K300, use K300 for new loan
- **Formula**: `amount = client's choice (up to available_security)`

### Security Return
- **When**: After loan completion
- **Purpose**: Return ALL remaining security to borrower
- **Constraint**: Returns full available amount
- **Formula**: `amount = available_security`

### Security Adjustment
- **When**: During active loan
- **Purpose**: Use security to pay down loan balance
- **Constraint**: Cannot exceed loan balance or available security
- **Formula**: `amount = min(available_security, loan_balance)`

## Balance Calculation

Security withdrawals **DECREASE** the security balance:

```python
# INCREASES to security balance:
upfront + topups + carry_forwards

# DECREASES to security balance:
adjustments + returned + withdrawals

# Final balance:
balance = (upfront + topups + carry_forwards) - (adjustments + returned + withdrawals)
```

## Vault Impact

When a withdrawal is approved:

```python
# Vault balance DECREASES (money goes OUT to borrower)
vault.balance -= withdrawal_amount

# Transaction recorded as:
{
    'transaction_type': 'security_return',  # Same as return
    'direction': 'out',
    'amount': withdrawal_amount,
    'description': 'Security return for LV-XXXXXX'
}
```

**Note**: Both withdrawals and returns use the same vault transaction type (`security_return`) because both represent money leaving the vault to go back to the borrower.

## User Interface

### For Loan Officers:
1. View loan details
2. See "Security Actions" section
3. Click "Withdrawal" button
4. Form shows:
   - Current available security
   - Minimum required security
   - Maximum withdrawal amount
   - Input field for withdrawal amount
   - Notes field

### For Managers:
1. Dashboard shows pending security transactions
2. Click to review withdrawal request
3. See:
   - Loan details
   - Borrower information
   - Requested amount
   - Current security status
   - Validation checks
4. Approve or Reject with optional notes

## Security Deposit Fields

```python
class SecurityDeposit:
    paid_amount = ...           # Total deposited
    security_used = ...         # Used for adjustments
    security_returned = ...     # Returned + Withdrawn
    
    @property
    def available_security(self):
        return paid_amount - security_used - security_returned
```

## Example Scenario


Palm Cash
Dashboard
Loans
Clients
Payments
Securities
Reports
8

Precious Nyawo
Loan Officer Dashboard
Welcome back, Precious Nyawo! Here's your performance overview.

Refreshes in 58s

Groups

3

Clients

3

Active Loans

0

Outstanding

K0

Today's Collections
Expected

K829

Amount due today

Collected

K8,708

Amount received

Pending

K0

Still to collect

Overdue

0

Loans with overdue payments

Record Payment
View Details
My Groups
+ New Group
Group Name	Members	Active Loans	Pending Payments	Action
apple	1	0	None	View
Orange	1	0	None	View
silver	1	0	None	View
View All Groups →
Quick Actions
View My Clients
Register Borrower
New Loan Application
Create Group
Record Payment
My Applications
Bulk Collection
Default Collection
Reports
History
My Performance
Processing Fees
Initiate Upfront Payment
Approved loans awaiting 10% upfront payment

No loans pending upfront payment.

Ready to Disburse
Upfront payment verified — disburse these loans now

No loans ready for disbursement yet.

Security Management
Overview of all security deposit activities

0

Pending

2

Adjustments

0

Top-Ups

2

Returns

1

Withdrawals

Security Deposit Actions
Adjustment · Return · Top-Up
Search client...

 apple 1

 silver 1

 Orange 1
Clients Expected to Pay Today
Search client...

 Orange 4

 silver 1

 apple 1
Processing Fees
0 pending
3 verified
All processing fees verified
Overdue Loans
Showing 0 of 0
0
Group

All Groups
Show Rows

5
View All
No overdue loans found with the selected filters.

Default Collections
0

Defaulted Loans

K0

Total Outstanding

K0

Collected This Month

Record Default Collection
Securities — Amount Summary
K600

Total Held

K0

Available

K200

Used (Adjustments)

K400

Returned

Full Securities Report
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

Powered by Palm Cash Team
**After Approval**:
- Security withdrawn: K300 (cash to client)
- Security returned: K300
- Available security: K700 (can be carried forward to new loan)
- Vault balance: -K300 (decreased)

**Next Step**:
- When client applies for new loan, the K700 can be carried forward
- No need to deposit new security if K700 covers 10% requirement

## Daily Loans Exception

**Important**: Daily loans do NOT have security deposits, so withdrawals are not applicable.

```python
if loan.repayment_frequency == 'daily':
    messages.error(request, 'Daily loans do not have security deposits.')
    return redirect(...)
```

## Database Records

### SecurityTransaction Table
```sql
INSERT INTO SecurityTransaction (
    loan_id,
    transaction_type,  -- 'withdrawal'
    amount,
    status,            -- 'pending' → 'approved'
    initiated_by,
    approved_by,
    notes,
    created_at
)
```

### VaultTransaction Table (after approval)
```sql
INSERT INTO VaultTransaction (
    transaction_type,  -- 'security_return'
    direction,         -- 'out'
    branch,
    amount,
    balance_after,
    description,
    loan_id,
    recorded_by,
    approved_by,
    transaction_date
)
```

## Error Messages

### Common Errors:

1. **"Security withdrawal can only be done on a completed loan."**
   - Loan status must be 'completed', not 'active'
   - Use 'adjustment' for active loans instead

2. **"No security deposit found for this loan."**
   - Loan doesn't have a security deposit record

3. **"Withdrawal amount must be greater than zero."**
   - Amount entered is 0 or negative

4. **"Withdrawal amount exceeds available security (KX.XX)."**
   - Trying to withdraw more than available
   - Maximum is the full available security amount

5. **"Daily loans do not have security deposits."**
   - Daily loans are exempt from security requirements

## Reports & Tracking

Withdrawals appear in:

1. **Securities Dashboard** (`/securities/`)
   - Shows withdrawal count and total amount
   - Filtered by branch/officer/group/client

2. **Loan Detail Page**
   - Security transactions history
   - Shows all withdrawals with status

3. **Manager Dashboard**
   - Pending withdrawals count
   - Requires approval

4. **Securities History** (`/payments/securities-history/`)
   - All security transactions including withdrawals
   - Filterable by type, status, date range

## Code Locations

### Main Files:
- **Initiation**: `loans/security_views.py` (security_action view)
- **Business Logic**: `loans/security_services.py` (initiate_security_withdrawal, approve_security_transaction)
- **Vault Recording**: `loans/vault_services.py` (record_security_return)
- **Model**: `loans/models.py` (SecurityTransaction, SecurityDeposit)
- **Template**: `loans/templates/loans/security_action.html`

### URL Routes:
```python
# Initiate withdrawal
path('loans/<int:loan_id>/security/<str:action>/', security_action, name='security_action')

# Approve/reject
path('security-transaction/<int:txn_id>/approve/', security_transaction_approve, name='security_transaction_approve')
```

## Summary

Security withdrawals allow clients to access part of their security deposit **after loan completion**, giving them flexibility to:
1. **Withdraw cash** for personal use
2. **Keep remaining security** to apply for a new loan (via carry forward)

This is different from:
- **Security Return**: Returns ALL remaining security (no new loan)
- **Security Adjustment**: Uses security to pay down an ACTIVE loan

The system has no minimum requirement for withdrawals - the client decides how much to withdraw and how much to keep for their next loan. All withdrawals require manager approval before funds are released from the vault.
