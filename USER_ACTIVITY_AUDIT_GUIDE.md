# User Activity Audit System - Implementation Guide

## Overview
The User Activity Audit System provides comprehensive tracking and monitoring of user actions, login sessions, and system activities. This feature is designed for administrators and managers to monitor user behavior, track critical actions, and maintain security compliance.

## Features Implemented

### 1. User List View (Audit Overview)
**URL**: `/accounts/audit/`

Displays a comprehensive list of system users with:
- Full Name
- Role (Administrator, Manager, Loan Officer)
- Last Login Time
- Number of actions performed today
- Current Status (Active/Offline)
- Clickable user names for drill-down

**Filters Available**:
- Search by name, username, or email
- Filter by role
- Filter by status (Active Now / Offline)

### 2. User Activity Dashboard
**URL**: `/accounts/audit/user/<user_id>/`

Detailed activity dashboard for each user showing:

**Top Section**:
- User Name
- Role
- Last Login Time
- Last Activity Time
- Current Status (Active / Offline with visual indicator)
- Session Duration

**Session Information**:
- Last Login
- Last Logout
- Session Duration (calculated)
- IP Address tracking

**Activity Summary**:
- Actions Today
- Actions This Week
- Number of Critical Actions

**Activity Timeline**:
- Chronological list of recent actions (last 20)
- Time-stamped entries
- Color-coded by severity

**Top Actions Chart**:
- Visual breakdown of most frequent actions
- Progress bars showing relative frequency

### 3. Activity Logs Table
Comprehensive log table with:
- Timestamp
- Action Type
- Target (client, loan, branch, etc.)
- Description
- Severity Level (Info, Warning, Critical)

**Filters**:
- Date Range (From/To)
- Action Type
- Severity Level
- Pagination (50 records per page)

### 4. Login Session Tracking
Recent login sessions table showing:
- Login Time
- Logout Time
- Session Duration
- IP Address
- Status (Active/Ended)

## Database Models

### UserLoginSession
Tracks user login/logout sessions:
```python
- user: ForeignKey to User
- login_time: DateTime
- logout_time: DateTime (nullable)
- ip_address: GenericIPAddressField
- user_agent: TextField
- session_key: CharField
- is_active: Boolean
```

### UserActivityLog
Unified activity log for all user actions:
```python
- user: ForeignKey to User
- action: CharField (50+ action types)
- target_type: CharField (client, loan, branch, etc.)
- target_id: CharField
- target_name: CharField
- description: TextField
- severity: CharField (info, warning, critical)
- timestamp: DateTime
- ip_address: GenericIPAddressField
- old_value: TextField
- new_value: TextField
```

## Action Types Tracked

### Authentication
- Login, Logout, Password Change

### User Management
- Create, Update, Delete, Activate, Deactivate User

### Branch Management
- Create, Update, Delete Branch

### Client Management
- Create, Update, Transfer, Assign Client

### Group Management
- Create, Update, Add/Remove Member

### Loan Management
- Apply, Approve, Reject, Disburse, Edit, Transfer Loan

### Payment Management
- Record, Confirm, Reject Payment
- Record Collection, Default Collection

### Security Deposits
- Create, Verify, Top-up, Return

### Document Management
- Upload, Verify, Delete Document

### Payroll
- Generate Payroll, Process Payment, Update Salary

### Reports & Views
- View Report, Export Report, View Dashboard

## Usage

### For Administrators

1. **Access User Audit**:
   - Navigate to Admin Dashboard
   - Click "User Activity" quick action
   - Or go to `/accounts/audit/`

2. **View User Activity**:
   - Click on any user name in the list
   - Review activity summary and timeline
   - Filter logs by date, action, or severity

3. **Monitor Active Users**:
   - Use status filter to see currently active users
   - Check session durations
   - Review recent actions

### For Developers

#### Logging User Activity

Use the helper function to log activities:

```python
from accounts.audit_views import log_user_activity

# Example: Log loan approval
log_user_activity(
    user=request.user,
    action='loan_approve',
    description=f'Approved loan {loan.application_number} for {loan.borrower.full_name}',
    target_type='loan',
    target_id=str(loan.id),
    target_name=loan.application_number,
    severity='critical',
    request=request
)
```

#### Logging Login/Logout

Login tracking is automatic via CustomLoginView. For manual tracking:

```python
from accounts.audit_views import log_login, log_logout

# Log login
log_login(user, request)

# Log logout
log_logout(user, request)
```

## Security Features

1. **IP Address Tracking**: All actions and sessions track IP addresses
2. **User Agent Logging**: Browser/device information captured
3. **Severity Levels**: Critical actions highlighted for review
4. **Immutable Logs**: Activity logs cannot be edited (admin read-only)
5. **Session Monitoring**: Active session detection (30-minute timeout)

## Access Control

- **Admins**: Full access to all user activity logs
- **Managers**: Full access to all user activity logs
- **Loan Officers**: No access
- **Borrowers**: No access

## Performance Considerations

1. **Database Indexes**: Optimized indexes on:
   - user + timestamp
   - action + timestamp
   - severity + timestamp
   - target_type + target_id

2. **Pagination**: 50 records per page to prevent slow queries

3. **Selective Loading**: Related data loaded efficiently with select_related

## Migration

Run the migration to create the new tables:

```bash
python manage.py migrate accounts
```

## Admin Interface

Both models are registered in Django Admin:
- UserLoginSession: View login/logout history
- UserActivityLog: View all activity logs (read-only)

## Future Enhancements

Potential additions:
1. Export audit logs to CSV/PDF
2. Email alerts for critical actions
3. Advanced analytics dashboard
4. Geolocation tracking
5. Failed login attempt tracking
6. Automated anomaly detection
7. Compliance report generation

## Testing

Test the feature:
1. Login as admin
2. Navigate to User Activity page
3. Perform various actions (create loan, approve, etc.)
4. Check that actions are logged
5. Verify filters work correctly
6. Test pagination
7. Check session tracking

## Troubleshooting

**Issue**: Login tracking not working
- **Solution**: Ensure CustomLoginView is being used in accounts/urls.py

**Issue**: No activity logs appearing
- **Solution**: Check that log_user_activity() is being called in views

**Issue**: Session duration shows "Unknown"
- **Solution**: Ensure logout is properly tracked with log_logout()

## Support

For issues or questions, contact the development team or refer to the main README.md.
