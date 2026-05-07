# Visual Guide: What You Should See

## 📊 Processing Fees Page

### Location
Dashboard → Processing Fees (Manager/Admin)

### What You Should See:

#### 1. Filter Section
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Search & Filter                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [Search Box]  [Officer ▼]  [Group ▼]  [Loan Type ▼]       │
│                                                             │
│ [From Date]   [To Date]   [🔍 Search]  [✖ Clear]          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Loan Type Dropdown Options:**
- All Types
- 📅 Daily
- 📆 Weekly

#### 2. Table Columns
```
┌──────┬────────┬──────────┬───────┬─────────┬──────┬───────┬────────┬────────────┬────────┐
│ Date │ App #  │ Borrower │ Group │ Officer │ Fee  │ Vault │ Status │ Verified By│ Action │
├──────┼────────┼──────────┼───────┼─────────┼──────┼───────┼────────┼────────────┼────────┤
│ 07   │ LA-001 │ John Doe │ Gray  │ Mary    │ K50  │ 📅    │ ✓      │ Manager    │   —    │
│ May  │        │          │       │         │      │ Daily │ Verified│ 06 May    │        │
├──────┼────────┼──────────┼───────┼─────────┼──────┼───────┼────────┼────────────┼────────┤
│ 06   │ LA-002 │ Jane Doe │ Pink  │ Grace   │ K75  │ 📆    │ ⏳     │     —      │ Verify │
│ May  │        │          │       │         │      │Weekly │ Pending│            │        │
└──────┴────────┴──────────┴───────┴─────────┴──────┴───────┴────────┴────────────┴────────┘
```

**Vault Column Shows:**
- 📅 Daily (blue badge) - for daily loans
- 📆 Weekly (purple badge) - for weekly loans

---

## 💰 Expense List Page

### Location
Dashboard → View Expenses (Manager/Admin)

### What You Should See:

#### 1. Filter Section
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Filter Expenses                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [Branch ▼]  [Start Date]  [End Date]  [Category ▼]        │
│                                                             │
│ [Vault Type ▼]  [🔍 Filter]                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Branch Dropdown (Admin Only):**
- All Branches
- Chazanga
- KAMWALA
- SOUTH KUKU
- MANDEVU BRANCH

**Vault Type Dropdown:**
- All Vaults
- 📅 Daily
- 📆 Weekly

#### 2. Table Columns
```
┌──────┬────────┬───────┬──────────┬─────────────┬────────┬─────────────┬─────────┐
│ Date │ Branch │ Vault │ Category │ Description │ Amount │ Recorded By │ Actions │
├──────┼────────┼───────┼──────────┼─────────────┼────────┼─────────────┼─────────┤
│ 07   │ Chaza  │ 📅    │ Fuel     │ Transport   │ K100   │ Manager     │   🗑️   │
│ May  │ -nga   │ Daily │          │ to bank     │        │             │         │
├──────┼────────┼───────┼──────────┼─────────────┼────────┼─────────────┼─────────┤
│ 06   │ Chaza  │ 📆    │ Office   │ Stationery  │ K50    │ Manager     │   🗑️   │
│ May  │ -nga   │Weekly │          │ supplies    │        │             │         │
└──────┴────────┴───────┴──────────┴─────────────┴────────┴─────────────┴─────────┘
```

**Vault Column Shows:**
- 📅 Daily (blue badge) - expense from daily vault
- 📆 Weekly (purple badge) - expense from weekly vault
- Unknown (gray text) - old expenses before dual-vault system

**Branch Column (Admin Only):**
- Shows which branch the expense belongs to
- Displayed as a badge with branch name

---

## 🏦 Vault Page

### Location
Dashboard → Branch Vault (Manager/Admin)

### What You Should See:

#### 1. Filter Section
```
┌─────────────────────────────────────────────────────────────┐
│ Filters                                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [Branch ▼]  [From Date]  [To Date]  [Type ▼]  [Vault ▼]   │
│                                                             │
│ [Direction ▼]  [Reversals ▼]  [Filter]  [Clear]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Vault Dropdown:**
- All Vaults
- Daily Vault
- Weekly Vault

**Important**: 
- Leaving dates EMPTY and clicking "Filter" should show ALL transactions
- This is correct behavior - empty filters = no filtering

#### 2. Table Columns
```
┌──────┬──────────────┬───────┬───────────┬────────┬──────────────┬──────┬────────┬────────────┬─────────┐
│ Date │ Type         │ Vault │ Direction │ Amount │ Balance After│ Loan │ Client │ Approved By│ Actions │
├──────┼──────────────┼───────┼───────────┼────────┼──────────────┼──────┼────────┼────────────┼─────────┤
│ 07   │ Security     │ 📆    │ ▲ IN      │ +K200  │ K400         │ LV-  │ Juster │     —      │ Reverse │
│ May  │ Deposit      │Weekly │           │        │              │ 00021│ Kaluba │            │         │
├──────┼──────────────┼───────┼───────────┼────────┼──────────────┼──────┼────────┼────────────┼─────────┤
│ 06   │ Loan         │ 📆    │ ▼ OUT     │ -K2000 │ K2,820       │ LV-  │ Doreen │ Mirriam    │ Reverse │
│ May  │ Disbursement │Weekly │           │        │              │ 00014│ Chanda │ Chanda     │         │
└──────┴──────────────┴───────┴───────────┴────────┴──────────────┴──────┴────────┴────────────┴─────────┘
```

**Vault Column Shows:**
- 📅 Daily (blue badge) - transaction in daily vault
- 📆 Weekly (purple badge) - transaction in weekly vault

---

## 🔍 How to Test Each Filter

### Test 1: Vault Date Filter
1. Go to **Branch Vault** page
2. Leave date fields EMPTY
3. Click **Filter** button
4. **Expected**: Should see ALL transactions (not 0)
5. Enter a date range (e.g., May 1 to May 7)
6. Click **Filter** button
7. **Expected**: Should see only transactions in that date range

### Test 2: Processing Fees Loan Type Filter
1. Go to **Processing Fees** page
2. Click **Loan Type** dropdown
3. Select **📅 Daily**
4. Click **Search** button
5. **Expected**: Should see only daily loan processing fees
6. Change to **📆 Weekly**
7. Click **Search** button
8. **Expected**: Should see only weekly loan processing fees

### Test 3: Expense Vault Type Filter
1. Go to **View Expenses** page
2. Click **Vault Type** dropdown
3. Select **📅 Daily**
4. Click **Filter** button
5. **Expected**: Should see only expenses from daily vault
6. Change to **📆 Weekly**
7. Click **Filter** button
8. **Expected**: Should see only expenses from weekly vault

### Test 4: Expense Branch Filter (Admin Only)
1. Go to **View Expenses** page (as admin)
2. Click **Branch** dropdown
3. Select a specific branch (e.g., "Chazanga")
4. Click **Filter** button
5. **Expected**: Should see only expenses from that branch
6. **Branch column** should show the selected branch name

---

## ❓ Common Issues and Solutions

### Issue 1: "I don't see the Vault column"
**Solution**: Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)

### Issue 2: "Vault column shows 'Unknown'"
**Explanation**: This is normal for old expenses created before the dual-vault system. New expenses will show the correct vault type.

### Issue 3: "Filter shows 0 results"
**Possible Causes**:
1. No records exist for that filter (try "All" to see if any records exist)
2. All records are in the other vault/type
3. Date range doesn't include any transactions

**Solution**: 
- Click "Clear" to reset all filters
- Try "All Vaults" or "All Types" first
- Check if you have any records at all

### Issue 4: "Date filter still shows 0 when empty"
**Solution**:
1. Hard refresh browser (Ctrl+Shift+R)
2. Clear browser cache completely
3. Check browser console (F12) for JavaScript errors
4. Try clicking "Clear" button instead of "Filter"

---

## 📝 Quick Reference

### Badge Colors

| Badge | Meaning | Color |
|-------|---------|-------|
| 📅 Daily | Daily vault/loan | Blue |
| 📆 Weekly | Weekly vault/loan | Purple |
| ▲ IN | Money coming in | Green |
| ▼ OUT | Money going out | Red |
| ✓ Verified | Processing fee verified | Green |
| ⏳ Pending | Processing fee pending | Amber/Yellow |

### Filter Behavior

| Filter | Empty Value | Behavior |
|--------|-------------|----------|
| Date From | (empty) | Shows all dates from beginning |
| Date To | (empty) | Shows all dates until now |
| Vault Type | "All Vaults" | Shows both daily and weekly |
| Loan Type | "All Types" | Shows both daily and weekly loans |
| Branch | "All Branches" | Shows all branches (admin only) |

---

## ✅ Final Checklist

Before reporting an issue, please verify:

- [ ] I have hard refreshed my browser (Ctrl+Shift+R)
- [ ] I have cleared my browser cache
- [ ] I am looking at the correct page (Vault vs Processing Fees vs Expenses)
- [ ] I have tried clicking "Clear" to reset filters
- [ ] I have verified that records exist (by viewing "All")
- [ ] I have checked the browser console (F12) for errors
- [ ] I have taken a screenshot showing the issue

If all checks pass and the issue persists, please provide:
1. Which page you're on
2. What filter you're using
3. What you expect to see
4. What you actually see
5. Screenshot of the issue
