# Role Permissions & Actions Guide

## Overview
This document explains what actions each role can perform when viewing dashboards, and what actions can be performed on behalf of others.

---

## 1. MANAGER VIEWING OFFICER DASHBOARD

### Current Status: **VIEW ONLY** ❌

When a manager views an officer's performance report, they can currently:

**✅ What Managers CAN Do:**
- View officer's performance metrics (disbursed, collected, completed loans, etc.)
- See officer's activity log (disbursements, collections, defaults, fees)
- Filter by date range and activity type
- Search for specific clients or loans
- Export/print the report

**❌ What Managers CANNOT Do (Currently):**
- Record payments on behalf of the officer
- Disburse loans on behalf of the officer
- Create loan applications for the officer
- Modify officer's transactions
- Approve/reject items as the officer

### Recommendation: Add "Act As Officer" Feature

Managers should be able to:
1. **Record Payments** - Record payments on behalf of officer
2. **Disburse Loans** - Disburse approved loans
3. **Create Applications** - Submit loan applications
4. **Manage Clients** - Add/edit clients in officer's groups
5. **Bulk Collection** - Perform bulk collection for officer's groups

---

## 2. ADMIN VIEWING MANAGER DASHBOARD

### Current Status: **FULL ACCESS** ✅

When an admin views a manager's dashboard, they have **FULL MANAGER PERMISSIONS**.

**✅ What Admins CAN Do (As Manager):**

### Security & Approvals
- ✅ Approve security deposits
- ✅ Approve security returns
- ✅ Approve security adjustments
- ✅ Approve security withdrawals
- ✅ Approve security top-ups
- ✅ View all pending approvals

### Payment Management
- ✅ Confirm pending payments
- ✅ Reject payments
- ✅ View payment history
- ✅ Perform bulk collection
- ✅ Collect default payments

### Loan Management
- ✅ View all branch loans
- ✅ Approve loan applications
- ✅ Disburse loans
- ✅ View loan schedules

### Client Management
- ✅ View all clients in branch
- ✅ View client details
- ✅ View groups and members

### Financial Operations
- ✅ Manage branch vault
- ✅ Inject capital
- ✅ Make bank withdrawals/deposits
- ✅ Transfer funds between branches
- ✅ Record expenses
- ✅ View expense history

### Processing Fees
- ✅ Verify processing fees
- ✅ View fee collection reports
- ✅ Manage pending fee verifications

### Reports & Analytics
- ✅ View branch performance
- ✅ View officer performance
- ✅ View collection reports
- ✅ View security transaction reports
- ✅ Export data

### Officer Management
- ✅ View officer statistics
- ✅ Assign officers to groups
- ✅ View officer performance metrics

**Implementation:**
- Admin sees banner: "Admin View Mode - You are viewing [Manager Name]'s dashboard"
- All actions are logged with admin's user ID
- Admin can switch back to branch selection view

---

## 3. MANAGER ACTING ON BEHALF OF LOAN OFFICER

### Current Status: **PARTIAL** ⚠️

**✅ What Managers CAN Do (On Behalf of Officer):**

### Payment Confirmation
- ✅ Confirm payments recorded by officer
- ✅ Reject payments recorded by officer
- ✅ View all officer's pending payments

### Security Approvals
- ✅ Approve security deposits collected by officer
- ✅ Approve security returns requested by officer
- ✅ Approve adjustments/withdrawals/top-ups

### Loan Approvals
- ✅ Approve loan applications submitted by officer
- ✅ Authorize loan disbursements

### Processing Fees
- ✅ Verify processing fees collected by officer

**❌ What Managers CANNOT Do (Currently):**
- ❌ Record payments as the officer
- ❌ Disburse loans as the officer
- ❌ Create loan applications as the officer
- ❌ Collect security deposits as the officer
- ❌ Perform bulk collection as the officer

### Recommendation: Add "Act As Officer" Feature

Managers should have a button on officer dashboard:
```
[Act As This Officer]
```

When clicked, manager can:
1. Record payments (logged as: "Recorded by Manager [Name] on behalf of Officer [Name]")
2. Disburse loans
3. Create loan applications
4. Collect security deposits
5. Perform bulk collection

---

## 4. PROPOSED PERMISSION MATRIX

| Action | Officer | Manager (Own) | Manager (On Behalf) | Admin (As Manager) |
|--------|---------|---------------|---------------------|-------------------|
| **Payments** |
| Record Payment | ✅ | ✅ | ❌ → ✅ | ✅ |
| Confirm Payment | ❌ | ✅ | ✅ | ✅ |
| Reject Payment | ❌ | ✅ | ✅ | ✅ |
| Bulk Collection | ✅ | ✅ | ❌ → ✅ | ✅ |
| **Loans** |
| Create Application | ✅ | ✅ | ❌ → ✅ | ✅ |
| Approve Loan | ❌ | ✅ | ✅ | ✅ |
| Disburse Loan | ✅ | ✅ | ❌ → ✅ | ✅ |
| **Security** |
| Collect Deposit | ✅ | ✅ | ❌ → ✅ | ✅ |
| Approve Deposit | ❌ | ✅ | ✅ | ✅ |
| Request Return | ✅ | ✅ | ❌ → ✅ | ✅ |
| Approve Return | ❌ | ✅ | ✅ | ✅ |
| **Clients** |
| Add Client | ✅ | ✅ | ❌ → ✅ | ✅ |
| Edit Client | ✅ | ✅ | ❌ → ✅ | ✅ |
| Create Group | ✅ | ✅ | ❌ → ✅ | ✅ |
| **Vault** |
| View Vault | ✅ | ✅ | ✅ | ✅ |
| Inject Capital | ❌ | ✅ | ❌ | ✅ |
| Bank Operations | ❌ | ✅ | ❌ | ✅ |
| **Reports** |
| View Own Performance | ✅ | ✅ | ✅ | ✅ |
| View Officer Performance | ❌ | ✅ | ✅ | ✅ |
| View Branch Reports | ❌ | ✅ | ✅ | ✅ |
| **Processing Fees** |
| Collect Fee | ✅ | ✅ | ❌ → ✅ | ✅ |
| Verify Fee | ❌ | ✅ | ✅ | ✅ |

**Legend:**
- ✅ = Currently allowed
- ❌ = Currently not allowed
- ❌ → ✅ = Should be added

---

## 5. IMPLEMENTATION RECOMMENDATIONS

### A. Add "Act As Officer" Button to Officer Dashboard

**Location:** Officer Performance Report page (when viewed by manager)

**Button:**
```html
<button class="px-4 py-2 bg-blue-600 text-white rounded-lg">
  <i class="fas fa-user-shield mr-2"></i>
  Act As This Officer
</button>
```

**Actions Available:**
1. Record Payment
2. Disburse Loan
3. Create Loan Application
4. Collect Security Deposit
5. Perform Bulk Collection
6. Add/Edit Clients

**Audit Trail:**
- All actions logged with: `performed_by=manager, on_behalf_of=officer`
- Notes field: "Action performed by Manager [Name] on behalf of Officer [Name]"

### B. Add Action Buttons to Officer Dashboard

**Current:** Only "View" buttons
**Proposed:** Add action buttons when manager is viewing

```html
<!-- In officer performance report -->
{% if user.role in ['manager', 'admin'] %}
<div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
  <h3 class="font-bold text-blue-900 mb-3">Manager Actions</h3>
  <div class="flex gap-2">
    <a href="{% url 'payments:record' %}?officer={{ officer.id }}" 
       class="px-4 py-2 bg-green-600 text-white rounded-lg">
      Record Payment
    </a>
    <a href="{% url 'loans:disburse_list' %}?officer={{ officer.id }}" 
       class="px-4 py-2 bg-blue-600 text-white rounded-lg">
      Disburse Loans
    </a>
    <a href="{% url 'payments:bulk_collection' %}?officer={{ officer.id }}" 
       class="px-4 py-2 bg-purple-600 text-white rounded-lg">
      Bulk Collection
    </a>
  </div>
</div>
{% endif %}
```

### C. Update Admin Manager View

**Current:** Admin has full access ✅
**Enhancement:** Add visual indicator for all actions

```html
<!-- Show on every action -->
<div class="text-xs text-blue-600 mt-1">
  <i class="fas fa-info-circle"></i>
  Acting as Manager: {{ manager.get_full_name }}
</div>
```

---

## 6. AUDIT TRAIL REQUIREMENTS

All actions performed on behalf of others must log:

```python
{
  "action": "record_payment",
  "performed_by": "Manager John Doe (ID: 123)",
  "on_behalf_of": "Officer Jane Smith (ID: 456)",
  "timestamp": "2026-05-21 14:30:00",
  "details": {
    "payment_number": "PAY-000200",
    "amount": 150.00,
    "client": "Mary Banda"
  }
}
```

---

## 7. SECURITY CONSIDERATIONS

### Permission Checks
```python
def can_act_as_officer(manager, officer):
    """Check if manager can act on behalf of officer"""
    # Manager must be in same branch
    if manager.branch != officer.branch:
        return False
    
    # Manager role required
    if manager.role not in ['manager', 'admin']:
        return False
    
    # Officer must be active
    if not officer.is_active:
        return False
    
    return True
```

### Action Logging
```python
def log_action_on_behalf(action, manager, officer, details):
    """Log action performed on behalf of another user"""
    ActionLog.objects.create(
        action_type=action,
        performed_by=manager,
        on_behalf_of=officer,
        details=details,
        timestamp=timezone.now()
    )
```

---

## 8. NEXT STEPS

To implement these features:

1. **Add "Act As Officer" functionality**
   - Create middleware to track "acting_as" user
   - Add session variable for "on_behalf_of"
   - Update all views to check and log

2. **Add action buttons to officer dashboard**
   - Update officer_performance_report.html
   - Add manager action section
   - Link to existing views with officer parameter

3. **Enhance audit logging**
   - Add "on_behalf_of" field to all models
   - Update signals to capture acting user
   - Add audit trail view

4. **Update permissions**
   - Modify permission decorators
   - Add "can_act_as" checks
   - Update role-based access control

---

## Questions?

If you want me to implement any of these features, let me know which ones to prioritize:

1. ⭐ **High Priority:** Manager can record payments on behalf of officer
2. ⭐ **High Priority:** Manager can perform bulk collection for officer
3. **Medium Priority:** Manager can disburse loans for officer
4. **Medium Priority:** Manager can create loan applications for officer
5. **Low Priority:** Enhanced audit trail view

Which would you like me to implement first?
