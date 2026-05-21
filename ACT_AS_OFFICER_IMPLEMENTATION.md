# Act As Officer Feature - Implementation Guide

## Overview
This feature allows managers and admins to "act as" a loan officer, seeing only that officer's clients, groups, and loans, and performing actions on their behalf.

## What Was Implemented

### 1. Middleware (`common/middleware.py`)
- **ActAsOfficerMiddleware**: Tracks which officer the manager is acting as
- Stores officer ID in session
- Validates permissions (same branch for managers, any branch for admins)
- Makes `request.acting_as_officer` available in all views

### 2. Views (`common/views.py`)
- **start_acting_as_officer**: Starts acting as a specific officer
  - Validates manager has permission
  - Sets session variables
  - Shows success message
- **stop_acting_as_officer**: Stops acting mode and returns to normal

### 3. URLs (`common/urls.py`)
- `/common/act-as-officer/<officer_id>/` - Start acting as officer
- `/common/stop-acting-as-officer/` - Stop acting as officer

### 4. Context Processor (`common/context_processors.py`)
- Makes `acting_as_officer` available in all templates
- Shows officer name and details in UI

### 5. UI Components

#### Global Banner (in `base_tailwind.html`)
- Fixed banner at top of page when acting as officer
- Shows officer name
- "Stop Acting" button
- Adjusts page padding automatically

#### Officer Dashboard (`officer_performance_report.html`)
- "Act As This Officer" button for managers
- Quick action buttons (Bulk Collection, Disburse Loans, etc.)
- Information note about scope restrictions
- Banner when already acting as officer

## How It Works

### For Managers:

1. **View Officer Dashboard**
   - Go to Dashboard → Manage Officers → Select Officer
   - Or view officer performance report

2. **Click "Act As This Officer"**
   - Button appears at top of officer's dashboard
   - Only visible to managers and admins

3. **Restricted Scope**
   - Manager now sees ONLY that officer's:
     - Clients
     - Groups
     - Loans
     - Payments
     - Collections

4. **Perform Actions**
   - Record payments
   - Disburse loans
   - Bulk collection
   - Create loan applications
   - All actions logged as: "Performed by Manager [Name] on behalf of Officer [Name]"

5. **Stop Acting**
   - Click "Stop Acting" in global banner
   - Returns to normal manager view

### For Admins:

- Same as managers, but can act as ANY officer in ANY branch
- No branch restriction

## Security & Permissions

### Permission Checks
```python
# Manager can only act as officers in their branch
if manager.role == 'manager':
    if manager_branch != officer_branch:
        # Access denied
        
# Admin can act as any officer
if user.role == 'admin':
    # Always allowed
```

### Session Management
```python
# Session variables set:
request.session['acting_as_officer_id'] = officer.id
request.session['acting_as_officer_name'] = officer.get_full_name()

# Available in views:
if request.acting_as_officer:
    # Filter data to this officer only
```

## Data Filtering (To Be Implemented)

When acting as an officer, all queries must be filtered:

### Clients
```python
if request.acting_as_officer:
    clients = User.objects.filter(
        role='borrower',
        group_memberships__group__officer_assignments__officer=request.acting_as_officer
    ).distinct()
```

### Groups
```python
if request.acting_as_officer:
    groups = BorrowerGroup.objects.filter(
        officer_assignments__officer=request.acting_as_officer
    )
```

### Loans
```python
if request.acting_as_officer:
    loans = Loan.objects.filter(
        loan_officer=request.acting_as_officer
    )
```

### Payments
```python
if request.acting_as_officer:
    payments = Payment.objects.filter(
        loan__loan_officer=request.acting_as_officer
    )
```

## Audit Trail

All actions performed while acting as an officer should be logged:

### Payment Recording
```python
payment = Payment.objects.create(
    # ... payment fields ...
    recorded_by=request.user,  # The manager
    notes=f"Recorded by {request.user.get_full_name()} on behalf of {request.acting_as_officer.get_full_name()}"
)
```

### Loan Disbursement
```python
loan.disbursed_by = request.user  # The manager
loan.notes += f"\nDisbursed by {request.user.get_full_name()} on behalf of {request.acting_as_officer.get_full_name()}"
loan.save()
```

## Next Steps - Views to Update

To complete the implementation, these views need to be updated to respect `acting_as_officer`:

### High Priority:
1. **Bulk Collection View** (`payments/views.py`)
   - Filter groups by acting officer
   - Show only their groups

2. **Payment Recording** (`payments/views.py`)
   - Filter clients by acting officer
   - Record payment with proper attribution

3. **Loan Disbursement** (`loans/views.py`)
   - Filter loans by acting officer
   - Disburse with proper attribution

4. **Client List** (`clients/views.py`)
   - Filter clients by acting officer
   - Show only their clients

### Medium Priority:
5. **Loan Application Creation** (`loans/views.py`)
   - Create application for acting officer's clients
   - Set loan_officer to acting officer

6. **Security Deposits** (`securities/views.py`)
   - Filter by acting officer's clients

7. **Payment History** (`payments/views.py`)
   - Show only acting officer's payments

### Low Priority:
8. **Reports** (various)
   - Filter all reports by acting officer

## Example Implementation

Here's how to update a view to respect acting_as_officer:

```python
@login_required
def bulk_collection(request):
    # Determine which officer's data to show
    if hasattr(request, 'acting_as_officer') and request.acting_as_officer:
        # Manager is acting as an officer
        officer = request.acting_as_officer
    elif request.user.role == 'loan_officer':
        # Officer viewing their own data
        officer = request.user
    else:
        # Manager/admin viewing all data
        officer = None
    
    # Filter groups
    if officer:
        groups = BorrowerGroup.objects.filter(
            officer_assignments__officer=officer,
            is_active=True
        )
    else:
        # Show all groups for manager's branch
        groups = BorrowerGroup.objects.filter(
            branch=request.user.branch,
            is_active=True
        )
    
    # ... rest of view logic ...
```

## Testing Checklist

- [ ] Manager can click "Act As Officer" button
- [ ] Session is set correctly
- [ ] Global banner appears
- [ ] Manager sees only officer's data
- [ ] Manager can record payments
- [ ] Manager can perform bulk collection
- [ ] Manager can disburse loans
- [ ] Actions are logged with proper attribution
- [ ] "Stop Acting" button works
- [ ] Session is cleared properly
- [ ] Manager from different branch cannot act as officer
- [ ] Admin can act as any officer
- [ ] Officer cannot act as another officer

## Deployment Steps

1. **Pull latest code**
   ```bash
   git pull origin main
   ```

2. **No migrations needed** (only middleware and views)

3. **Clear Python cache**
   ```bash
   find . -name "*.pyc" -delete
   ```

4. **Restart server**
   ```bash
   sudo systemctl restart gunicorn
   ```

5. **Test the feature**
   - Login as manager
   - Go to officer dashboard
   - Click "Act As This Officer"
   - Verify banner appears
   - Try performing actions
   - Click "Stop Acting"

## Known Limitations

1. **Views not yet updated**: Most views don't filter by acting_as_officer yet
   - This needs to be added to each view individually
   - See "Next Steps" section above

2. **No audit log view**: Actions are logged in notes, but no dedicated audit view
   - Consider adding an audit trail page

3. **No time limit**: Acting mode persists until manually stopped
   - Consider adding auto-timeout after X hours

## Future Enhancements

1. **Auto-timeout**: Automatically stop acting after 2 hours
2. **Audit Trail Page**: Dedicated page showing all "act as" actions
3. **Permission Granularity**: Allow/deny specific actions while acting
4. **Notification**: Notify officer when manager acts on their behalf
5. **Activity Log**: Show what actions were performed while acting

## Questions?

If you need help:
1. Updating specific views to respect acting_as_officer
2. Adding audit trail functionality
3. Implementing auto-timeout
4. Any other enhancements

Let me know which views you want me to update first!
