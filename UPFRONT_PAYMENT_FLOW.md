# Upfront Payment Flow - Complete Guide

## Current Status
The diagnostic shows:
- **Total SecurityDeposit records: 0**
- **Loans with upfront payment recorded: 0**

This means **no upfront payments have been submitted yet**.

## How Upfront Payments Should Work

### Step 1: Loan is Approved
- Loan status changes to 'approved'
- System calculates upfront payment required (10% of principal)
- Loan officer notifies borrower about upfront payment requirement

### Step 2: Borrower Submits Upfront Payment
- Borrower logs in
- Goes to their loan details
- Clicks "Submit Upfront Payment"
- Fills in:
  - Amount (minimum 10% of loan)
  - Payment method (Mobile Money, Bank Transfer, Cash, Other)
  - Payment reference (transaction ID)
  - Optional: Payment proof (receipt)
  - Optional: Notes
- Submits the form

### Step 3: System Records Payment
When the form is submitted:
1. `Loan.upfront_payment_paid` is set to the amount
2. `Loan.upfront_payment_date` is set to current time
3. `Loan.upfront_payment_verified` is set to False
4. Loan is saved
5. Signal fires and creates `SecurityDeposit` record with `is_verified=False`
6. Notification is sent to loan officer

### Step 4: Manager Reviews and Approves
- Manager goes to Pending Approvals
- Sees the pending security deposit
- Reviews the payment details
- Clicks "Approve" or "Reject"
- If approved: `SecurityDeposit.is_verified = True`
- If rejected: Payment is reset

## URL Routes

**For Borrower to Submit Payment:**
```
/loans/<loan_id>/upfront-payment/
```

**For Manager to Verify Payment:**
```
/dashboard/pending-approvals/
```

## What's Missing

Based on the diagnostic, no upfront payments have been submitted. This could be because:

1. **No loans have been approved yet**
   - Check if any loans have status='approved'
   - If not, approve a test loan first

2. **Borrowers don't know how to submit payment**
   - They need to go to their loan details
   - Look for "Submit Upfront Payment" button
   - Fill in the form

3. **The form isn't accessible**
   - Check if borrowers can access `/loans/<id>/upfront-payment/`
   - Check if they have permission to submit

## Testing the Flow

### Step 1: Create a Test Loan
```bash
python manage.py shell
from loans.models import Loan
from accounts.models import User
from decimal import Decimal

# Get a borrower and loan officer
borrower = User.objects.filter(role='borrower').first()
officer = User.objects.filter(role='loan_officer').first()

# Create a test loan
loan = Loan.objects.create(
    borrower=borrower,
    loan_officer=officer,
    principal_amount=Decimal('10000'),
    status='approved',
    application_number='TEST-001'
)
print(f"Created loan {loan.id}")
exit()
```

### Step 2: Submit Upfront Payment
```bash
python manage.py shell
from loans.models import Loan

loan = Loan.objects.get(id=1)  # Replace with actual loan ID
print(f"Loan {loan.id}: upfront_required={loan.upfront_payment_required}")
print(f"URL: /loans/{loan.id}/upfront-payment/")
exit()
```

Then visit that URL in your browser and submit a payment.

### Step 3: Check if Payment Was Recorded
```bash
python manage.py shell
from loans.models import Loan, SecurityDeposit

loan = Loan.objects.get(id=1)
print(f"Loan {loan.id}:")
print(f"  upfront_payment_paid: {loan.upfront_payment_paid}")
print(f"  upfront_payment_verified: {loan.upfront_payment_verified}")

try:
    deposit = loan.security_deposit
    print(f"  SecurityDeposit: {deposit.id}, is_verified={deposit.is_verified}")
except:
    print(f"  SecurityDeposit: NOT CREATED")
exit()
```

### Step 4: Check Pending Approvals
```bash
python manage.py shell
from loans.models import SecurityDeposit

deposits = SecurityDeposit.objects.filter(is_verified=False)
print(f"Pending deposits: {deposits.count()}")
for deposit in deposits:
    print(f"  - Loan {deposit.loan.id}: {deposit.paid_amount}")
exit()
```

## Next Steps

1. **Verify loans are approved:**
   ```bash
   python manage.py shell
   from loans.models import Loan
   approved = Loan.objects.filter(status='approved')
   print(f"Approved loans: {approved.count()}")
   exit()
   ```

2. **If no approved loans, approve one:**
   - Go to Django admin
   - Find a loan with status='pending'
   - Change status to 'approved'
   - Save

3. **Have a borrower submit an upfront payment:**
   - Log in as a borrower
   - Go to their loan details
   - Click "Submit Upfront Payment"
   - Fill in the form
   - Submit

4. **Run the diagnostic again:**
   ```bash
   python manage.py shell < check_pending_approvals.py
   ```

5. **Check pending approvals page:**
   - Go to /dashboard/pending-approvals/
   - Should now show pending security deposits

## Files Involved

- **Form**: `palmcash/loans/forms_upfront.py`
- **View**: `palmcash/loans/views.py::UpfrontPaymentView`
- **Model**: `palmcash/loans/models.py::Loan, SecurityDeposit`
- **Signal**: `palmcash/loans/signals.py::create_security_deposit`
- **URL**: `palmcash/loans/urls.py`
- **Template**: `palmcash/loans/templates/loans/upfront_payment.html`

## Troubleshooting

**Problem: Form not submitting**
- Check browser console for JavaScript errors
- Check Django error log
- Verify form validation passes

**Problem: Payment recorded but no SecurityDeposit created**
- Check if signal is registered
- Check if loan status is 'approved'
- Check if signal handler has errors

**Problem: SecurityDeposit created but not showing in pending approvals**
- Check if is_verified is False
- Check if manager's branch matches officer's branch
- Check if officer has OfficerAssignment

## Summary

The system is working correctly - it's just waiting for:
1. Loans to be approved
2. Borrowers to submit upfront payments
3. Managers to review and approve them

Once a borrower submits an upfront payment, it will automatically appear in the pending approvals page.
