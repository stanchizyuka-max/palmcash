# Loan Workflow & Manager Responsibilities

## Complete Loan Lifecycle

```
1. BORROWER APPLIES
   ↓
   Loan Status: 'pending'
   
2. MANAGER APPROVES LOAN
   ↓
   Loan Status: 'approved'
   Manager Action: Click "Approve Loan" button
   
3. BORROWER SUBMITS UPFRONT PAYMENT (10%)
   ↓
   Loan.upfront_payment_paid = amount
   Loan.upfront_payment_verified = False
   SecurityDeposit created (pending verification)
   
4. MANAGER VERIFIES UPFRONT PAYMENT
   ↓
   Loan Status: still 'approved'
   SecurityDeposit.is_verified = True
   Manager Action: Go to "Pending Approvals" → Approve Security Deposit
   
5. MANAGER DISBURSES LOAN
   ↓
   Loan Status: 'disbursed' → 'active'
   Loan.disbursement_date = now
   PaymentSchedule records created automatically
   Manager Action: Click "Disburse Loan" button
   
6. BORROWER MAKES PAYMENTS
   ↓
   Loan Status: 'active'
   PaymentCollection records created
   
7. LOAN COMPLETED
   ↓
   Loan Status: 'completed'
   All payments made
```

## Manager Actions Required

### 1. Loan Approval
**Where**: Loan Detail Page → Actions Section
**What**: Review loan application and approve
**When**: After borrower submits application
**Result**: Loan status changes to 'approved'

### 2. Upfront Payment Verification
**Where**: Dashboard → Pending Approvals → Security Deposits
**What**: Verify that borrower paid 10% upfront
**When**: After borrower submits upfront payment
**Result**: SecurityDeposit.is_verified = True

### 3. Loan Disbursement
**Where**: Loan Detail Page → Actions Section
**What**: Disburse the approved loan to borrower
**When**: After upfront payment is verified
**Result**: 
- Loan status changes to 'active'
- PaymentSchedule created automatically
- Borrower can now see payment schedule

## Current Issues

### Issue 1: Loan Showing as "Completed" Without Payment Schedule
**Cause**: Loan status is 'completed' but PaymentSchedule was never created
**Why**: Loan was never properly disbursed (status never changed to 'active')
**Fix**: 
1. Manager must approve the loan
2. Borrower must submit upfront payment
3. Manager must verify upfront payment
4. Manager must disburse the loan

### Issue 2: "No Payment Schedule Available"
**Cause**: PaymentSchedule is only created when loan is disbursed
**Why**: Loan is still in 'approved' or 'pending' status
**Fix**: Complete the disbursement process (see above)

## Manager Dashboard - Pending Approvals Section

The manager dashboard shows:
- **Pending Loan Approvals**: Loans waiting for manager approval
- **Pending Security Deposits**: Upfront payments waiting for verification
- **Ready to Disburse**: Loans ready for disbursement

### Quick Actions for Managers
1. **Approve Security** - Verify upfront payments
2. **View Collections** - See payment collections
3. **Manage Officers** - Manage loan officers
4. **View Expenses** - Track expenses
5. **Verify Users** - Verify user documents
6. **Verify Documents** - Review client documents
7. **Manage Users** - Manage system users

## Loan Status Flow

```
pending → approved → disbursed → active → completed
                  ↓
              rejected
                  ↓
              defaulted
```

**pending**: Loan application submitted, awaiting manager approval
**approved**: Manager approved, awaiting upfront payment and disbursement
**disbursed**: Loan disbursed, payment schedule created
**active**: Borrower is making payments
**completed**: All payments made, loan finished
**rejected**: Manager rejected the application
**defaulted**: Borrower defaulted on payments

## What Needs to Be Fixed

1. **Add Manager Loan Approval Interface**
   - Show pending loans on manager dashboard
   - Allow manager to approve/reject loans
   - Show loan details for review

2. **Add Manager Upfront Payment Verification**
   - Show pending upfront payments
   - Allow manager to verify/reject
   - Update SecurityDeposit status

3. **Add Manager Disbursement Interface**
   - Show approved loans ready for disbursement
   - Allow manager to disburse
   - Automatically create payment schedule

4. **Fix Loan Status Logic**
   - Ensure loans don't show as 'completed' without payment schedule
   - Validate status transitions
   - Prevent invalid state combinations

## Testing the Workflow

### Step 1: Create a Test Loan
1. Log in as borrower
2. Go to Loans → Apply for Loan
3. Fill in details and submit
4. Loan status: 'pending'

### Step 2: Manager Approves
1. Log in as manager
2. Go to Loans → View Loan
3. Click "Approve Loan"
4. Loan status: 'approved'

### Step 3: Borrower Submits Upfront Payment
1. Log in as borrower
2. Go to Dashboard → Upfront Payments Required
3. Click "Submit Payment"
4. Enter 10% of loan amount
5. SecurityDeposit created with is_verified=False

### Step 4: Manager Verifies Upfront Payment
1. Log in as manager
2. Go to Dashboard → Pending Approvals
3. Find the security deposit
4. Click "Approve"
5. SecurityDeposit.is_verified = True

### Step 5: Manager Disburses Loan
1. Log in as manager
2. Go to Loans → View Loan
3. Click "Disburse Loan"
4. Loan status: 'active'
5. PaymentSchedule created

### Step 6: Borrower Sees Payment Schedule
1. Log in as borrower
2. Go to Loans → View Loan
3. Should now see payment schedule
4. Can make payments

## Files to Update

- `palmcash/palmcash/dashboard/views.py` - Add manager loan management views
- `palmcash/palmcash/dashboard/templates/dashboard/manager_enhanced.html` - Add loan management section
- `palmcash/palmcash/loans/views.py` - Ensure proper status transitions
- `palmcash/palmcash/loans/models.py` - Add validation for status transitions

