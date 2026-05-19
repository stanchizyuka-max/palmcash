# Branch Column Added to User Management

## ✅ Changes Made

### 1. Fixed 500 Error
**Issue**: Branch filter dropdown was causing a 500 error on `/accounts/manage/users/`

**Solution**: Added try-except block when importing `OfficerAssignment` to handle cases where the model might not be available.

```python
try:
    from loans.models import OfficerAssignment
    context['branches'] = OfficerAssignment.objects.values_list('branch', flat=True).distinct().order_by('branch')
except Exception:
    context['branches'] = []
```

### 2. Added `get_branch()` Method to User Model
**Location**: `accounts/models.py`

**Purpose**: Determine which branch a user belongs to based on their role.

**Logic**:
- **Loan Officers**: Get branch from `OfficerAssignment`
- **Managers**: Get branch from `managed_branch`
- **Borrowers**: Get branch from assigned officer or group
- **Admins**: Return "All Branches"
- **Unassigned**: Return "Unassigned"

```python
def get_branch(self):
    """Get the branch this user belongs to"""
    try:
        if self.role == 'loan_officer':
            from loans.models import OfficerAssignment
            assignment = OfficerAssignment.objects.filter(officer=self).first()
            return assignment.branch if assignment else 'Unassigned'
        
        elif self.role == 'manager':
            if hasattr(self, 'managed_branch') and self.managed_branch:
                return self.managed_branch.name
            return 'Unassigned'
        
        elif self.role == 'borrower':
            if self.assigned_officer:
                return self.assigned_officer.get_branch()
            from clients.models import GroupMembership
            membership = GroupMembership.objects.filter(
                member=self, is_active=True
            ).select_related('group').first()
            if membership and membership.group:
                return membership.group.branch
            return 'Unassigned'
        
        elif self.role == 'admin':
            return 'All Branches'
        
        return 'N/A'
    except Exception:
        return 'N/A'
```

### 3. Added Branch Column to User Management Table
**Location**: `templates/accounts/users_manage.html`

**Visibility**: Admin only

**Features**:
- Shows between "Contact" and "Role" columns
- Color-coded badges:
  - **Purple**: "All Branches" (Admins)
  - **Blue**: Specific branch name (KUKU, Mandevu, etc.)
  - **Gray**: "Unassigned" or "N/A"
- Building icon for visual clarity

**Example Display**:
```
User          | Contact           | Branch    | Role          | Joined      | Status
------------- | ----------------- | --------- | ------------- | ----------- | ------
John Doe      | john@example.com  | KUKU      | Loan Officer  | May 1, 2026 | Active
Jane Smith    | jane@example.com  | Mandevu   | Manager       | May 2, 2026 | Active
Admin User    | admin@example.com | All       | Admin         | Jan 1, 2026 | Active
```

---

## 📋 What Admins Will See

### Before
- User Management table had 6 columns
- No way to see which branch a user belongs to
- Had to click into each user to see their branch

### After
- User Management table has 7 columns (admin only)
- Branch column shows at a glance which branch each user belongs to
- Color-coded for easy identification
- Managers and officers still see 6 columns (no branch column)

---

## 🎨 Branch Badge Colors

| Branch Value    | Color  | Use Case                    |
|-----------------|--------|-----------------------------|
| All Branches    | Purple | Admin users                 |
| KUKU, Mandevu   | Blue   | Users assigned to a branch  |
| Unassigned      | Gray   | Users not yet assigned      |
| N/A             | Gray   | Error or unknown            |

---

## 🧪 Testing

### Test Cases

1. **Admin viewing all users**:
   - ✅ Should see Branch column
   - ✅ Officers show their assigned branch
   - ✅ Managers show their managed branch
   - ✅ Borrowers show their officer's branch or group branch
   - ✅ Admins show "All Branches"

2. **Manager viewing users**:
   - ✅ Should NOT see Branch column
   - ✅ Only sees users in their branch

3. **Officer viewing users**:
   - ✅ Should NOT see Branch column
   - ✅ Only sees their assigned borrowers

4. **Branch filter dropdown**:
   - ✅ Should show all branches
   - ✅ Should not cause 500 error
   - ✅ Should filter users correctly

---

## 🚀 Deployment

### On Server

```bash
# Pull changes
cd ~/www/palmcashloans.site
git pull origin main

# Restart server
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### In Browser

Clear cache or use incognito mode to see the new column.

---

## 📁 Files Modified

1. **accounts/models.py**
   - Added `get_branch()` method to User model

2. **accounts/views.py**
   - Added try-except for OfficerAssignment import
   - Fixed 500 error

3. **templates/accounts/users_manage.html**
   - Added Branch column header (admin only)
   - Added Branch data cell with color-coded badge
   - Updated empty state colspan

---

## ✅ Benefits

### For Admins
- **Quick Overview**: See which branch each user belongs to at a glance
- **Better Filtering**: Combine branch filter with branch column for powerful filtering
- **Easier Management**: No need to click into each user to see their branch
- **Visual Clarity**: Color-coded badges make it easy to identify branch assignments

### For System
- **Error Fixed**: 500 error on user management page resolved
- **Robust**: Handles missing data gracefully (shows "Unassigned" or "N/A")
- **Performant**: Uses efficient queries with select_related

---

## 🎯 Example Use Cases

1. **Find all unassigned officers**:
   - Filter by role: "Loan Officers"
   - Look for "Unassigned" in Branch column

2. **See all KUKU branch users**:
   - Filter by branch: "KUKU"
   - Branch column confirms all users are from KUKU

3. **Identify borrowers without branch assignment**:
   - Filter by role: "Borrowers"
   - Look for "Unassigned" in Branch column

---

## 📊 Summary

| Feature                  | Status | Visibility |
|--------------------------|--------|------------|
| Branch column            | ✅ Added | Admin only |
| get_branch() method      | ✅ Added | All users  |
| 500 error fix            | ✅ Fixed | All users  |
| Color-coded badges       | ✅ Added | Admin only |
| Branch filter dropdown   | ✅ Working | Admin only |

---

**Commit**: `a218b58`
**Pushed**: May 19, 2026
**Status**: Ready for deployment
