# Transaction Reversal Guide

## Overview

The transaction reversal feature allows managers and admins to correct mistaken vault entries while maintaining a complete audit trail.

## How It Works

### Step 1: Find the Mistaken Transaction

Go to **Branch Vault** and locate the transaction you want to reverse.

### Step 2: Click "Reverse" Button

In the Actions column, click the **"Reverse"** button for that transaction.

### Step 3: Provide Reason

A modal will appear asking for:
- Transaction details (shown automatically)
- **Reason for reversal** (required)

Example reasons:
- "Duplicate entry - already recorded"
- "Wrong amount entered"
- "Wrong transaction type"
- "Recorded in wrong vault (daily vs weekly)"

### Step 4: Confirm Reversal

Click **"Reverse Transaction"** to confirm.

## What Happens

### The System Creates:

1. **Reversal Transaction** with:
   - Opposite direction (IN becomes OUT, OUT becomes IN)
   - Same amount
   - Description: "REVERSAL: [original description] | Reason: [your reason]"
   - Reference number: REV-XXXXXXXX
   - Current date/time
   - Recorded by: You

2. **Vault Balance Update**:
   - Automatically adjusted to cancel the original transaction
   - Correct balance restored

## Visual Example

### Scenario: Accidentally Recorded K500 Twice

**Original Vault:**
```
Date       | Type          | Direction | Amount  | Balance After
03 May     | Cash Deposit  | ▲ IN      | +K500   | K1,500
03 May     | Cash Deposit  | ▲ IN      | +K500   | K2,000  ← Duplicate (mistake)
```

**After Reversing the Duplicate:**
```
Date       | Type          | Direction | Amount  | Balance After | Description
04 May     | Cash Deposit  | ▼ OUT     | -K500   | K1,500        | REVERSAL: Cash Deposit | Reason: Duplicate entry
03 May     | Cash Deposit  | ▲ IN      | +K500   | K2,000        | Cash Deposit
03 May     | Cash Deposit  | ▲ IN      | +K500   | K1,500        | Cash Deposit
```

Balance corrected from K2,000 back to K1,500 ✅

## How to Identify Reversals

Reversal transactions are easy to spot:

1. **Description starts with "REVERSAL:"**
2. **Reference number starts with "REV-"**
3. **Opposite direction** from the original
4. **Includes the reason** in the description

## Important Notes

### ✅ What Reversals DO:

- Create an opposite transaction to cancel the mistake
- Maintain complete audit trail
- Show who reversed and when
- Include the reason for reversal
- Correct the vault balance

### ❌ What Reversals DON'T DO:

- Delete the original transaction (it remains visible)
- Hide the mistake (both transactions are visible)
- Allow editing of amounts (creates exact opposite)

## Common Use Cases

### 1. Duplicate Entry
**Problem:** Recorded the same deposit twice
**Solution:** Reverse one of the duplicate transactions
**Reason:** "Duplicate entry - already recorded"

### 2. Wrong Amount
**Problem:** Recorded K1,000 instead of K100
**Solution:** 
1. Reverse the K1,000 transaction
2. Record a new K100 transaction
**Reason:** "Wrong amount - should be K100"

### 3. Wrong Transaction Type
**Problem:** Recorded as "Cash Deposit" instead of "Bank Withdrawal"
**Solution:**
1. Reverse the wrong transaction
2. Record the correct transaction type
**Reason:** "Wrong transaction type - should be Bank Withdrawal"

### 4. Wrong Vault
**Problem:** Recorded in Daily vault instead of Weekly vault
**Solution:**
1. Reverse the transaction in Daily vault
2. Record it in the correct Weekly vault
**Reason:** "Recorded in wrong vault - should be Weekly"

## Permissions

- **Managers:** Can reverse transactions in their own branch
- **Admins:** Can reverse transactions in any branch

## Best Practices

1. **Always provide a clear reason** - helps with auditing
2. **Reverse as soon as you notice** - easier to track
3. **Don't reverse loan-related transactions** without checking the loan status first
4. **Document complex reversals** - add notes if needed

## Audit Trail

All reversals are tracked:
- Original transaction remains visible
- Reversal transaction shows who, when, and why
- Vault balance history is preserved
- Can be exported to CSV for reporting

## Questions?

If you're unsure whether to reverse a transaction:
1. Check with your manager/admin
2. Document the situation
3. Consider if a new transaction would be clearer than a reversal

## Related Features

- **Vault Dashboard:** View all transactions
- **Export CSV:** Download transaction history
- **Month Closing:** Locks transactions for the month
- **Vault History:** View historical balances
