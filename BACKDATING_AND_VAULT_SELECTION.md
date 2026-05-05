# Backdating and Vault Selection Features

## What Was Added

### 1. Expense Recording Improvements

**Vault Type Selection:**
- Expenses can now be recorded in **Daily Vault** or **Weekly Vault**
- Previously, all expenses went to Weekly Vault only
- Gives flexibility based on expense type

**Backdating Support:**
- Can now record expenses with past dates
- Date field defaults to today but can be changed
- Useful for recording expenses that were missed

**How It Works:**
1. Go to **Add Expense**
2. Select the date when expense occurred (can be last week, last month, etc.)
3. Choose which vault to deduct from (Daily or Weekly)
4. The vault transaction will use the expense date, not today's date

### 2. Other Vault Transactions

**Already Support Vault Selection:**
- ✅ Bank Withdrawal
- ✅ Bank Deposit
- ✅ Fund Received
- ✅ Branch Transfer
- ✅ Collection
- ✅ Savings Deposit/Withdrawal

**Need Backdating Added:**
- ⚠️ Bank Withdrawal
- ⚠️ Bank Deposit
- ⚠️ Fund Received
- ⚠️ Collection

These currently record with today's date. If you need backdating for these, let me know!

## Benefits

### 1. Accurate Record Keeping
- Record transactions on the actual date they occurred
- No more "recorded late" notes needed
- Vault history reflects real timeline

### 2. Flexibility
- Catch up on missed entries
- Correct timing of transactions
- Better month-end reconciliation

### 3. Proper Vault Management
- Choose appropriate vault for each expense
- Daily expenses → Daily Vault
- Weekly/monthly expenses → Weekly Vault

## Examples

### Example 1: Backdated Expense

**Scenario:** You forgot to record K500 fuel expense from last Monday

**Steps:**
1. Go to Add Expense
2. Amount: K500
3. Category: Transport/Fuel
4. **Date: Select last Monday's date**
5. Vault: Daily Vault
6. Save

**Result:**
- Expense recorded with last Monday's date
- Vault transaction shows last Monday's date
- Vault balance adjusted correctly

### Example 2: Choosing Vault Type

**Scenario:** Recording different types of expenses

**Daily Vault Expenses:**
- Small daily operational costs
- Fuel
- Office supplies
- Petty cash

**Weekly Vault Expenses:**
- Salaries
- Rent
- Utilities
- Large purchases

## Important Notes

### Vault Balance Calculation

When you backdate a transaction:
- The transaction appears in chronological order
- The "Balance After" reflects the balance at that point in time
- Current vault balance is still correct

### Month Closing

If you've already closed a month:
- You can still add backdated transactions for that month
- The closed month balance won't change
- New transactions appear in the history

### Audit Trail

All backdated transactions show:
- The actual transaction date (when it occurred)
- Who recorded it
- When it was recorded (created_at timestamp)

## Future Enhancements

If needed, we can add:
1. **Transaction date field** to all vault operations
2. **Bulk import** for multiple backdated transactions
3. **Date range restrictions** (e.g., can't backdate more than 30 days)
4. **Approval workflow** for backdated transactions

## Questions?

**Q: Can I backdate to last year?**
A: Yes, but be careful with closed months. Check with your manager first.

**Q: Will backdating affect reports?**
A: Yes, reports will include backdated transactions in the correct time period.

**Q: Can I change the date of an existing transaction?**
A: No, you need to reverse it and create a new one with the correct date.

**Q: What if I choose the wrong vault?**
A: Reverse the transaction and record it again in the correct vault.
