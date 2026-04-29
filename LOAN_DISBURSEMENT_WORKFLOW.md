# Loan Disbursement Workflow - Complete Guide

## Overview
**IMPORTANT:** Security deposits are handled differently based on loan type:
- **Daily Loans:** NO security deposit required
- **Weekly Loans:** 10% security deposit required

## Complete Workflow

### For DAILY LOANS (Simplified - No Security)

#### Step 1: Submit Loan Application
**Who:** Loan Officer  
**Action:** Submit loan application with frequency = "Daily"

#### Step 2: Record Processing Fee
**Who:** Loan Officer  
**Action:** Record the processing fee amount

#### Step 3: Verify Processing Fee
**Who:** Manager  
**Action:** Verify the processing fee was received

#### Step 4: Approve Loan Application
**Who:** Manager  
**Action:** Approve the loan application
- System creates Loan record
- System auto-creates security deposit with K0 (marked as verified)
- Loan status: **"Ready to Disburse"** immediately
- ✅ No security deposit step needed!

#### Step 5: Disburse Loan
**Who:** Loan Officer  
**Action:** Disburse the loan funds
- Check vault has sufficient balance
- Click "Disburse Loan"
- Loan becomes "Active"

---

### For WEEKLY LOANS (Full Process - Security Required)

#### Step 1: Submit Loan Application
**Who:** Loan Officer  
**Action:** Submit loan application with frequency = "Weekly"

#### Step 2: Record Processing Fee
**Who:** Loan Officer  
**Action:** Record the processing fee amount

#### Step 3: Verify Processing Fee
**Who:** Manager  
**Action:** Verify the processing fee was received

#### Step 4: Approve Loan Application
**Who:** Manager  
**Action:** Approve the loan application
- System creates Loan record
- System checks for security carry forward from previous completed loans
- If previous security exists and covers 10%:
  - ✅ Security automatically carried forward
  - ✅ Loan marked as "Ready to Disburse"
  - ✅ Skip to Step 7 (Disburse)
- If no previous security or insufficient:
  - ⏭️ Continue to Step 5 (Initiate Upfront Payment)

#### Step 5: Initiate 10% Upfront Payment (Security Deposit)
**Who:** Loan Officer  
**Action:** Record that borrower paid 10% security deposit
- Calculate 10% of loan amount
- Record payment received
- Status: "Pending Verification"

#### Step 6: Verify Upfront Payment (Security Deposit)
**Who:** Manager  
**Action:** Verify the 10% security deposit was received
- Review the amount
- Confirm cash was received
- Click "Verify"
- Security deposit marked as verified
- Loan status: "Ready to Disburse"

#### Step 7: Disburse Loan
**Who:** Loan Officer  
**Action:** Disburse the loan funds
- Check vault has sufficient balance
- Click "Disburse Loan"
- Loan becomes "Active"

---

## Security Deposit Requirements Summary

### Daily Loans:
- ❌ **NO security deposit required**
- ✅ Manager approves → Officer disburses immediately
- ✅ Faster disbursement process
- ✅ Better for short-term, small loans

### Weekly Loans:
- ✅ **10% security deposit required**
- ✅ Security can be carried forward from completed loans
- ✅ Protects against default on longer-term loans
- ✅ Security can be withdrawn after loan completion

## Key Differences: Daily vs Weekly Loans

### Daily Loans:
- Interest Rate: 40%
- Duration: Entered in **days** (e.g., 30 days)
- Payment Frequency: Daily
- **Security: NOT REQUIRED** ✨
- Workflow: Apply → Fee → Approve → **Disburse** (4 steps)

### Weekly Loans:
- Interest Rate: 45%
- Duration: Entered in **weeks** (e.g., 21 weeks)
- Payment Frequency: Weekly
- **Security: 10% REQUIRED**
- Workflow: Apply → Fee → Approve → Security → Verify → Disburse (6 steps)

## Validation Rules

### Cannot Approve Loan Application If:
- ❌ Processing fee not verified by manager

### Cannot Disburse Daily Loan If:
- ❌ Vault has insufficient balance
- ❌ Loan not in "approved" status

### Cannot Disburse Weekly Loan If:
- ❌ Security deposit not verified
- ❌ Vault has insufficient balance
- ❌ Loan not in "approved" status

## Why Different Requirements?

**Daily Loans:**
- Short duration (typically 30-60 days)
- Smaller amounts
- Quick turnaround needed
- Lower risk due to short term
- **No security needed** - faster for clients and officers

**Weekly Loans:**
- Longer duration (typically 21+ weeks = 5+ months)
- Larger amounts
- Higher risk due to longer term
- **Security required** - protects institution

## Date: April 29, 2026
