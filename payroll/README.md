# Payroll Module - Setup & Usage Guide

## Overview
The Payroll module provides secure, role-based access control for managing employee salaries and payment information.

## Features
- ✅ Employee salary management
- ✅ Payment history tracking
- ✅ Role-based access control
- ✅ Audit logging for security
- ✅ Permission-based UI restrictions
- ✅ Multi-layer security (decorators, middleware, templates)

## Installation Steps

### 1. Run Migrations
```bash
python manage.py migrate payroll
```

This creates the following tables:
- `payroll_employee` - Employee records
- `payroll_salaryrecord` - Salary information
- `payroll_payrollpayment` - Payment history
- `payroll_payrollauditlog` - Security audit trail

### 2. Grant Payroll Access to Specific Admin

#### Option A: Using Management Command (Recommended)
```bash
# Grant access
python manage.py grant_payroll_access admin_username

# Revoke access
python manage.py grant_payroll_access admin_username --revoke
```

#### Option B: Using Django Admin Interface
1. Go to `/admin/accounts/user/`
2. Click on the specific admin user
3. Scroll to "User permissions" section
4. Add these permissions:
   - `payroll | employee | Can view payroll information`
   - `payroll | employee | Can manage payroll records`
5. Save

#### Option C: Using Web Interface (Easiest)
1. Login as superuser
2. Go to Admin Dashboard
3. Click "Payroll Access" in Quick Actions
4. Click "Grant Access" for the desired admin
5. Done!

#### Option D: Using Python Shell
```python
python manage.py shell

from django.contrib.auth.models import Permission
from accounts.models import User

# Find the admin user
admin = User.objects.get(username='your_admin_username')

# Get permissions
view_perm = Permission.objects.get(codename='can_view_payroll')
manage_perm = Permission.objects.get(codename='can_manage_payroll')

# Grant permissions
admin.user_permissions.add(view_perm, manage_perm)

# Verify
print(f"Has payroll access: {admin.has_perm('payroll.can_view_payroll')}")
```

## Access Control

### Permission Levels

1. **Super Admin** (is_superuser=True)
   - Full access to all payroll features
   - Can grant/revoke payroll access to others
   - Access to payroll management interface

2. **Finance Manager** (with permissions)
   - Can view and manage payroll
   - Can view salary details
   - Can process payments

3. **System Admin** (without permissions)
   - NO access to payroll
   - Payroll link hidden in navigation
   - Direct URL access blocked

### Security Layers

1. **View Decorators** - `@payroll_permission_required`
2. **Template Conditionals** - `{% if perms.payroll.can_view_payroll %}`
3. **URL Protection** - Automatic via decorators
4. **Audit Logging** - All access tracked

## Usage

### Accessing Payroll

1. **Via Navigation Menu**
   - Users with permission see "Payroll" in top navigation
   - Click to access payroll dashboard

2. **Via Admin Dashboard**
   - Superusers see "Payroll Access" in Quick Actions
   - Manage who can access payroll

3. **Direct URL**
   - `/payroll/` - Main dashboard
   - `/payroll/employees/` - Employee list
   - `/payroll/payments/` - Payment history
   - `/payroll/audit-logs/` - Security logs

### Managing Employees

Currently, employees must be created via Django Admin:
1. Go to `/admin/payroll/employee/`
2. Click "Add Employee"
3. Select user, enter employee ID, department, position
4. Save

### Adding Salary Records

Via Django Admin:
1. Go to `/admin/payroll/salaryrecord/`
2. Click "Add Salary Record"
3. Select employee, enter salary details
4. Save

### Recording Payments

Via Django Admin:
1. Go to `/admin/payroll/payrollpayment/`
2. Click "Add Payment"
3. Select employee, salary record, enter payment details
4. Save

## Audit Trail

All payroll access is logged automatically:
- Who accessed what
- When they accessed it
- From which IP address
- What action they performed

View audit logs at: `/payroll/audit-logs/`

## Testing

### Test Access Control

1. **Test as user WITHOUT permission:**
   - Login as regular admin
   - Payroll link should NOT appear in navigation
   - Accessing `/payroll/` should show "Access Denied"

2. **Test as user WITH permission:**
   - Grant permission using one of the methods above
   - Logout and login again
   - Payroll link should appear in navigation
   - Can access all payroll features

3. **Test audit logging:**
   - Access payroll features
   - Check `/payroll/audit-logs/`
   - Your actions should be logged

## Troubleshooting

### "Permission not found" error
Run migrations: `python manage.py migrate payroll`

### Payroll link not showing
1. Logout and login again (permissions are cached)
2. Verify permission: `python manage.py shell`
   ```python
   from accounts.models import User
   user = User.objects.get(username='your_username')
   print(user.has_perm('payroll.can_view_payroll'))
   ```

### Access denied even with permission
Clear browser cache and logout/login again

## Future Enhancements

- Bulk salary updates
- Payroll period management
- Tax calculations
- Export to Excel/PDF
- Email notifications
- Approval workflows
- Branch-level payroll filtering

## Security Notes

- All salary data is sensitive - only grant access to trusted users
- Audit logs cannot be deleted (read-only)
- IP addresses are logged for security
- Consider enabling two-factor authentication for payroll users
- Regular audit log reviews recommended
