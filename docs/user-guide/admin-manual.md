# Administrator Manual - Palm Cash

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Dashboard Overview](#dashboard-overview)
3. [User Management](#user-management)
4. [Branch Management](#branch-management)
5. [System Configuration](#system-configuration)
6. [Reports and Analytics](#reports-and-analytics)
7. [Security and Audit](#security-and-audit)
8. [Troubleshooting](#troubleshooting)

---

## 1. Introduction

### Role Overview
As an Administrator, you have full access to the Palm Cash system. You are responsible for:
- Managing all users across all branches
- Configuring system settings
- Monitoring system health
- Generating system-wide reports
- Ensuring data security and compliance

### Access Level
- ✅ View all branches
- ✅ Manage all users
- ✅ Access all reports
- ✅ Configure system settings
- ✅ View audit logs

---

## 2. Dashboard Overview

### Accessing the Dashboard
1. Log in with your admin credentials
2. You'll be directed to the Admin Dashboard
3. Dashboard shows system-wide statistics

### Dashboard Widgets

#### Key Metrics
- **Total Users**: All users in the system
- **Active Loans**: Currently active loans
- **Total Collections**: Today's collections
- **Pending Approvals**: Loans awaiting approval
- **Vault Balance**: Total cash across all branches

#### Quick Actions
- Add New User
- View Pending Approvals
- Generate Reports
- System Settings

---

## 3. User Management

### Viewing All Users

**Path**: Dashboard → User Management

#### Features
- **Search**: Search by name, phone, email, username, or NRC
- **Filter by Branch**: View users from specific branches
- **Filter by Role**: Borrowers, Officers, Managers, Admins
- **Filter by Status**: Active or Inactive users

#### User List Columns
- **User**: Name and username
- **Contact**: Email and phone number
- **Branch**: Assigned branch
- **Role**: User role
- **Joined**: Registration date
- **Status**: Active/Inactive
- **Actions**: View, Edit, Deactivate

### Adding a New User

#### Step 1: Navigate to Add User
1. Go to User Management
2. Click "Add New User" button

#### Step 2: Fill User Details
- **First Name**: User's first name
- **Last Name**: User's last name
- **Username**: Unique username
- **Email**: Valid email address
- **Phone**: Zambian mobile number (055, 057, 095, 096, 097, 076, 077)
- **Role**: Select role (Admin, Manager, Officer, Borrower)
- **Branch**: Assign to branch (if applicable)

#### Step 3: Set Password
- Enter a strong password
- Confirm password
- User will receive login credentials

#### Step 4: Activate User
- Check "Active" to enable login
- Click "Save"

### Editing User Details

1. Find the user in User Management
2. Click the edit icon (pencil)
3. Update required fields
4. Click "Save Changes"

### Deactivating a User

1. Find the user in User Management
2. Click the deactivate icon
3. Confirm deactivation
4. User will no longer be able to log in

### Assigning Users to Branches

#### For Loan Officers
1. Edit the officer's profile
2. Go to "Officer Assignment" section
3. Select branch
4. Set max groups and clients
5. Save changes

#### For Managers
1. Edit the manager's profile
2. Go to "Branch Management" section
3. Select managed branch
4. Save changes

---

## 4. Branch Management

### Viewing Branches

**Path**: Dashboard → Branches

#### Branch Information
- Branch name
- Branch manager
- Number of officers
- Number of clients
- Active loans
- Vault balance

### Adding a New Branch

1. Go to Branches
2. Click "Add Branch"
3. Enter branch details:
   - Branch name
   - Location
   - Manager (select from managers)
4. Click "Save"

### Managing Branch Officers

1. Go to specific branch
2. View assigned officers
3. Add/remove officers
4. Set officer limits

---

## 5. System Configuration

### General Settings

**Path**: Dashboard → Settings → General

#### Configurable Options
- **System Name**: Display name
- **Currency**: ZMW (Zambian Kwacha)
- **Date Format**: DD/MM/YYYY
- **Time Zone**: Africa/Lusaka
- **Language**: English

### Loan Settings

**Path**: Dashboard → Settings → Loans

#### Interest Rates
- **Daily Loans**: 40% interest
- **Weekly Loans**: 45% interest

#### Loan Limits
- **Minimum Loan**: K500
- **Maximum Loan**: K50,000
- **Processing Fee**: Configurable

#### Approval Workflow
- **Require Manager Approval**: Yes/No
- **Auto-approve under**: Amount threshold

### Payment Settings

**Path**: Dashboard → Settings → Payments

#### Payment Options
- **Allow Partial Payments**: Yes/No
- **Grace Period**: Days
- **Late Payment Fee**: Amount or percentage

### Notification Settings

**Path**: Dashboard → Settings → Notifications

#### Notification Types
- **In-App Notifications**: Enabled
- **Email Notifications**: Enabled/Disabled
- **SMS Notifications**: Enabled/Disabled

#### Notification Events
- Loan approval/rejection
- Payment confirmation
- Payment due reminders
- Overdue notifications

---

## 6. Reports and Analytics

### Available Reports

#### 1. Loan Portfolio Report
**Path**: Dashboard → Reports → Loan Portfolio

**Information**:
- Total loans
- Active loans
- Completed loans
- Defaulted loans
- Total disbursed amount
- Outstanding balance

**Filters**:
- Date range
- Branch
- Loan officer
- Loan status

#### 2. Collection Report
**Path**: Dashboard → Reports → Collections

**Information**:
- Daily collections
- Weekly collections
- Monthly collections
- Collection by officer
- Collection by branch

**Filters**:
- Date range
- Branch
- Officer

#### 3. Vault Report
**Path**: Dashboard → Reports → Vault

**Information**:
- Opening balance
- Total inflows
- Total outflows
- Closing balance
- Transaction details

**Filters**:
- Date range
- Branch
- Transaction type

#### 4. Performance Report
**Path**: Dashboard → Reports → Performance

**Information**:
- Officer performance
- Branch performance
- Collection rates
- Default rates
- Portfolio at risk

**Filters**:
- Date range
- Branch
- Officer

### Generating Reports

1. Navigate to Reports section
2. Select report type
3. Set filters (date range, branch, etc.)
4. Click "Generate Report"
5. View report on screen
6. Export to PDF or Excel

### Scheduling Reports

1. Go to report settings
2. Click "Schedule Report"
3. Set frequency (daily, weekly, monthly)
4. Set recipients (email addresses)
5. Save schedule

---

## 7. Security and Audit

### User Activity Logs

**Path**: Dashboard → Audit → User Activity

#### Tracked Activities
- Login/logout
- User creation/modification
- Loan approvals
- Payment confirmations
- Settings changes

#### Log Information
- User
- Action
- Timestamp
- IP address
- Details

### Security Settings

**Path**: Dashboard → Settings → Security

#### Password Policy
- Minimum length: 8 characters
- Require uppercase: Yes/No
- Require numbers: Yes/No
- Require special characters: Yes/No
- Password expiry: Days

#### Session Settings
- Session timeout: Minutes
- Concurrent sessions: Allowed/Not allowed
- Remember me: Enabled/Disabled

### Backup and Recovery

#### Automatic Backups
- **Frequency**: Daily at 2:00 AM
- **Retention**: 30 days
- **Location**: Secure cloud storage

#### Manual Backup
1. Go to Settings → Backup
2. Click "Create Backup Now"
3. Wait for completion
4. Download backup file

#### Restore from Backup
1. Go to Settings → Backup
2. Click "Restore"
3. Select backup file
4. Confirm restoration
5. System will restart

---

## 8. Troubleshooting

### Common Issues

#### Issue: User Cannot Log In
**Solutions**:
1. Check if user is active
2. Verify password is correct
3. Check if account is locked
4. Reset password if needed

#### Issue: Branch Filter Not Working
**Solutions**:
1. Clear browser cache
2. Check if branches are assigned
3. Verify OfficerAssignment records
4. Restart server if needed

#### Issue: Reports Not Generating
**Solutions**:
1. Check date range is valid
2. Verify data exists for filters
3. Check server logs for errors
4. Try different report format

#### Issue: Slow Performance
**Solutions**:
1. Check server resources
2. Optimize database queries
3. Clear old logs
4. Restart application server

### Getting Help

#### Support Channels
- **Email**: support@palmcash.com
- **Phone**: +260 XXX XXX XXX
- **Documentation**: docs.palmcash.com
- **GitHub Issues**: github.com/palmcash/issues

#### Emergency Contacts
- **System Administrator**: admin@palmcash.com
- **Technical Support**: tech@palmcash.com
- **On-call Support**: +260 XXX XXX XXX

---

## 📝 Best Practices

### User Management
- ✅ Regularly review user accounts
- ✅ Deactivate unused accounts
- ✅ Enforce strong passwords
- ✅ Monitor user activity
- ✅ Keep user information updated

### Security
- ✅ Change default passwords
- ✅ Enable two-factor authentication (when available)
- ✅ Review audit logs regularly
- ✅ Limit admin access
- ✅ Keep system updated

### Data Management
- ✅ Verify backups regularly
- ✅ Clean up old data
- ✅ Monitor database size
- ✅ Archive completed loans
- ✅ Maintain data integrity

### System Maintenance
- ✅ Apply updates promptly
- ✅ Monitor system performance
- ✅ Review error logs
- ✅ Test backup restoration
- ✅ Document changes

---

## 📞 Quick Reference

### Keyboard Shortcuts
- **Ctrl + K**: Quick search
- **Ctrl + /**: Help menu
- **Ctrl + S**: Save (in forms)
- **Esc**: Close modal

### Important URLs
- **Dashboard**: `/dashboard/`
- **User Management**: `/accounts/manage/users/`
- **Reports**: `/reports/`
- **Settings**: `/settings/`
- **Audit Logs**: `/audit/`

---

**Manual Version**: 1.0
**Last Updated**: May 19, 2026
**For System Version**: 1.0
