# Manager Dashboard - Visual Guide to Pending Counts

## Overview
This guide shows where all pending counts are displayed on the manager dashboard and how to access them.

## Dashboard Layout (Top to Bottom)

### 1. Header Section
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Manager Dashboard                                        │
│ Branch: KUKU | Welcome, Manager Name!                       │
│ Today: Saturday, May 30, 2026                               │
└─────────────────────────────────────────────────────────────┘
```

### 2. Key Metrics Row
```
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│ Officers │  Groups  │ Clients  │Disbursed │Collection│
│    12    │    45    │   234    │  K50,000 │  85.5%   │
└──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 3. Processing Fees & Vault Balances
```
┌─────────────────────────┬─────────────────────────────────┐
│ Fees This Month         │ Branch Vaults                   │
│ K12,500                 │ K150,000 Total                  │
│ K2,300 pending          │ Daily: K80,000 | Weekly: K70,000│
└─────────────────────────┴─────────────────────────────────┘
```

### 4. Today's Collections
```
┌─────────────────────────────────────────────────────────────┐
│ 📅 Today's Collections                                      │
├──────────────────┬──────────────────┬──────────────────────┤
│ Expected         │ Collected        │ Pending              │
│ K25,000          │ K18,500          │ K6,500               │
└──────────────────┴──────────────────┴──────────────────────┘
```

### 5. ⭐ ACTION REQUIRED SUMMARY (NEW)
**Displays when any pending items exist**

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️  Action Required                                         │
│ You have pending items that need your attention             │
├──────────┬──────────┬──────────┬──────────┬───────────────┤
│ Security │ Payments │   Loan   │  Appli-  │  Documents    │
│   Txns   │          │ Approvals│  cations │               │
│    8     │    12    │    5     │    3     │      7        │
│ [Click]  │ [Click]  │ [Click]  │ [Click]  │   [View]      │
└──────────┴──────────┴──────────┴──────────┴───────────────┘
```

**Features**:
- Amber/orange gradient background with warning icon
- Only shows when there are pending items
- Each card is clickable and links to the review page
- Shows counts for all pending item types

### 6. Pending Approvals - Security Transactions
```
┌─────────────────────────────────────────────────────────────┐
│ 🛡️  Pending Approvals                            [8]        │
│ Security transactions awaiting your action                  │
├──────────┬──────────┬──────────┬──────────────────────────┤
│ Returns  │Adjustmts │Withdrawls│ Top-Ups                   │
│    3     │    2     │    1     │    2                      │
└──────────┴──────────┴──────────┴──────────────────────────┘
│ [Review All] →                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7. Pending Payments + Loans Overview
```
┌─────────────────────────────┬─────────────────────────────┐
│ ⏰ Pending Payments         │ 💰 Loans Overview           │
│                             │                             │
│        12                   │ Active: 45  | Completed: 23│
│ payments awaiting           │ Pending: 8  | Total: 76    │
│ your confirmation           │                             │
│                             │                             │
│ [Review] →                  │ [View All] →                │
└─────────────────────────────┴─────────────────────────────┘
```

### 8. ⭐ ADDITIONAL PENDING ITEMS (NEW)
**Three new dedicated count cards**

```
┌──────────────────┬──────────────────┬──────────────────────┐
│ 📝 Loan Approvals│ 📄 Applications  │ ✅ Documents         │
│        [5]       │        [3]       │        [7]           │
│                  │                  │                      │
│       5          │       3          │       7              │
│ loans awaiting   │ pending loan     │ documents awaiting   │
│ manager approval │ applications     │ verification         │
│                  │                  │                      │
│                  │                  │ 45 of 120 verified   │
│                  │                  │ (37.5%)              │
│                  │                  │                      │
│ [Review & Approve│ [View Applications│                     │
└──────────────────┴──────────────────┴──────────────────────┘
```

**Card Details**:

#### Loan Approvals (Indigo)
- **Icon**: 📝 fa-file-signature
- **Shows**: Count of loans awaiting manager approval
- **Action**: "Review & Approve" button
- **Links to**: Pending approvals page

#### Applications (Purple)
- **Icon**: 📄 fa-file-alt
- **Shows**: Count of pending loan applications
- **Action**: "View Applications" button
- **Links to**: Application list page

#### Documents (Teal)
- **Icon**: ✅ fa-file-check
- **Shows**: Count of documents awaiting verification
- **Extra Info**: Verification rate (X of Y verified - Z%)
- **No action button**: Display only

### 9. Expenses and Funds
```
┌─────────────────────────────┬─────────────────────────────┐
│ 🧾 Expenses                 │ 💱 Funds Management         │
│ This Month: K8,500          │ Transfers: K25,000          │
│                             │ Deposits: K15,000           │
│ [Add Expense] →             │ [View History] →            │
└─────────────────────────────┴─────────────────────────────┘
```

### 10. Quick Actions Grid
```
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│View All  │ Approve  │ Approved │  View    │ Manage   │
│Clients   │ Security │ Deposits │Collections│Officers  │
└──────────┴──────────┴──────────┴──────────┴──────────┘
... (more quick action buttons)
```

## Count Summary Table

| Count Type | Variable Name | Display Location | Color | Action Link |
|------------|---------------|------------------|-------|-------------|
| **Security Transactions** | `pending_sec_txns_total` | 1. Action Banner<br>2. Pending Approvals Card | Orange | `pending_approvals` |
| **Payments** | `pending_payments_count` | 1. Action Banner<br>2. Pending Payments Card | Yellow | `payments:list` |
| **Loan Approvals** | `pending_loan_approvals` | 1. Action Banner<br>2. Loan Approvals Card | Indigo | `pending_approvals` |
| **Applications** | `pending_applications_count` | 1. Action Banner<br>2. Applications Card | Purple | `loans:application_list` |
| **Documents** | `pending_document_verifications` | 1. Action Banner<br>2. Documents Card | Teal | None (display only) |
| **Processing Fees** | `fees_total_pending` | Processing Fees Card | Violet | `manager_processing_fees` |

## Color Coding System

### Existing Colors
- 🔵 **Blue**: Officers, Expected Collections
- 🟢 **Green**: Groups, Collected, Active Loans
- 🟣 **Purple**: Clients
- 🟠 **Orange**: Disbursed, Security Approvals, Expenses
- 🔴 **Red**: Collection Rate
- 🟡 **Yellow**: Pending Collections, Pending Payments
- 🟣 **Violet**: Processing Fees
- 💚 **Emerald**: Vault Balances

### New Colors
- 🔷 **Indigo**: Loan Approvals (new)
- 🟪 **Purple**: Applications (new)
- 🔷 **Teal**: Documents (new)
- 🟧 **Amber**: Action Required Banner (new)

## Responsive Behavior

### Desktop (lg screens)
- Action Banner: 5 cards in a row
- Additional Pending Items: 3 cards in a row

### Tablet (md screens)
- Action Banner: 3 cards per row (wraps to 2 rows)
- Additional Pending Items: 2 cards per row (wraps)

### Mobile (sm screens)
- Action Banner: 2 cards per row
- Additional Pending Items: 1 card per column (stacks)

## User Workflow

### Scenario 1: Manager Logs In
1. See "Action Required" banner if items are pending
2. Quickly scan all pending counts
3. Click on highest priority item
4. Review and approve/process items
5. Return to dashboard to see updated counts

### Scenario 2: Checking Specific Count
1. Scroll to relevant section
2. View detailed count in dedicated card
3. Click action button to review items
4. Process items as needed

### Scenario 3: Daily Review
1. Check "Today's Collections" section
2. Review "Action Required" banner
3. Process each pending type systematically
4. Verify all counts are zero or acceptable

## Benefits of New Layout

### Before
- ❌ Had to navigate to multiple pages to check counts
- ❌ No visibility of loan approvals on dashboard
- ❌ No visibility of applications on dashboard
- ❌ No visibility of document verifications on dashboard
- ❌ Counts calculated but hidden

### After
- ✅ All counts visible at a glance
- ✅ Action Required banner for immediate attention
- ✅ Dedicated cards for each count type
- ✅ Direct links to review pages
- ✅ Verification rate tracking
- ✅ Consistent, professional UI

## Quick Reference

### To Check Pending Items
1. **Security Transactions**: Orange "Pending Approvals" section
2. **Payments**: Yellow "Pending Payments" card
3. **Loan Approvals**: Indigo card in "Additional Pending Items"
4. **Applications**: Purple card in "Additional Pending Items"
5. **Documents**: Teal card in "Additional Pending Items"
6. **Processing Fees**: Violet card in Key Metrics row

### To Take Action
- Click "Review All" on Security Approvals
- Click "Review" on Pending Payments
- Click "Review & Approve" on Loan Approvals
- Click "View Applications" on Applications
- Documents are view-only (no direct action link)

## Notes

- All counts are filtered by manager's branch
- Counts update in real-time after approvals
- Action Required banner only shows when items exist
- All cards maintain consistent styling
- Mobile-responsive design ensures usability on all devices
