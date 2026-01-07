# Loan Approval Guide

## Issue
Accessing `/loans/1/approve` directly in the browser doesn't work.

## Why
The approve endpoint is **POST-only**. You cannot access it with a GET request (which is what happens when you visit a URL in your browser).

## How to Approve a Loan

### Step 1: Go to Loan Detail Page
Visit: `https://stan13.pythonanywhere.com/loans/1/`

### Step 2: Check Your Permissions
You must be one of:
- **Admin** - Can always approve loans
- **Manager** - Can always approve loans  
- **Loan Officer** - Must manage at least 15 active groups

### Step 3: Check Loan Status
The loan must be in **'pending'** status to be approved.

If the loan is already 'approved', 'rejected', 'disbursed', etc., you cannot approve it again.

### Step 4: Click Approve Button
On the loan detail page, scroll to the "Actions" section and click the green "Approve Loan" button.

### Step 5: Confirm
A confirmation dialog will appear. Click "OK" to confirm the approval.

## Loan Approval Flow

```
Borrower applies for loan
        ↓
Loan status = 'pending'
        ↓
Loan Officer/Admin reviews
        ↓
Click "Approve Loan" button (POST request)
        ↓
Loan status = 'approved'
        ↓
Borrower receives approval notification
        ↓
Borrower submits upfront payment (10% of loan)
        ↓
Manager verifies upfront payment
        ↓
Loan ready for disbursement
```

## Loan Officer Requirements

If you're a **Loan Officer**, you need:
- At least **15 active groups** assigned to you
- To be able to approve loans

**Check your eligibility:**
1. Go to the loan detail page
2. Look for the "Active Groups Managed" box
3. If it shows "✅ Eligible", you can approve
4. If it shows "❌ Not Eligible", you need more groups assigned

## Troubleshooting

### "You do not have permission to approve loans"
- You must be an admin, manager, or loan officer
- If you're a loan officer, you need 15+ active groups

### "Loan officers must manage at least 15 active groups"
- You're a loan officer but don't have enough groups
- Contact your manager to assign more groups

### Approve button is disabled/grayed out
- You're a loan officer without 15+ groups
- Contact your manager

### Loan is not in 'pending' status
- The loan has already been approved, rejected, or is in another status
- You can only approve loans that are 'pending'

## API Endpoint Details

**Endpoint:** `POST /loans/<loan_id>/approve/`

**Required:**
- CSRF token (automatically included in forms)
- User must be logged in
- User must have appropriate role

**Optional:**
- `approval_notes` - Add notes to the approval (via POST data)

**Response:**
- Redirects to loan detail page
- Shows success message
- Sends email to borrower
- Creates in-app notification

## Example: Using cURL (Advanced)

If you want to approve via command line:

```bash
# Get CSRF token first
curl -c cookies.txt https://stan13.pythonanywhere.com/loans/1/

# Extract CSRF token from cookies or HTML

# Submit approval
curl -b cookies.txt \
  -X POST \
  -d "csrfmiddlewaretoken=YOUR_CSRF_TOKEN&approval_notes=Approved" \
  https://stan13.pythonanywhere.com/loans/1/approve/
```

## Common Mistakes

❌ **Wrong:** Visiting `https://stan13.pythonanywhere.com/loans/1/approve/` in browser
✅ **Right:** Go to `https://stan13.pythonanywhere.com/loans/1/` and click the Approve button

❌ **Wrong:** Trying to approve a loan that's already approved
✅ **Right:** Only approve loans with 'pending' status

❌ **Wrong:** Loan officer with 5 groups trying to approve
✅ **Right:** Loan officer with 15+ groups can approve

