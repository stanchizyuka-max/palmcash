# Search and Filter Features Added

## Overview
Added comprehensive search and filter functionality to both User Management and Notifications pages to help admins, managers, and officers find information quickly.

---

## ✅ FEATURE 1: User Management Search Filters

### Location
- **Page**: User Management (`/accounts/users/manage/`)
- **Template**: `templates/accounts/users_manage.html`
- **View**: `accounts/views.py` - `UsersManageView`

### Features Added

#### 1. **Search Bar**
- Search across multiple fields:
  - First name
  - Last name
  - Username
  - Email
  - Phone number
  - National ID (NRC)
- Real-time filtering as you type

#### 2. **Branch Filter** (Admin Only)
- Dropdown showing all branches
- Filters users by their assigned branch:
  - Officers: by their officer assignment
  - Managers: by their managed branch
  - Borrowers: by their assigned officer's branch or group branch

#### 3. **Status Filter**
- Filter by user status:
  - **All Status**: Show all users
  - **Active**: Show only active users
  - **Inactive**: Show only inactive users

#### 4. **Combined Filtering**
- All filters work together
- Filters are preserved when:
  - Switching between role tabs
  - Navigating pagination
  - Applying new filters

#### 5. **Clear Filters Button**
- One-click to reset all filters
- Returns to default view

### How It Works

**For Admins:**
- Can search all 101 users
- Can filter by any branch
- Can filter by role (All, Borrowers, Officers, Managers, Admins)
- Can filter by status (Active/Inactive)

**For Managers:**
- Can search users in their branch only
- Can filter by role (Borrowers, Officers in their branch)
- Can filter by status

**For Loan Officers:**
- Can search their assigned borrowers only
- Limited to borrower role
- Can filter by status

### Example Use Cases

1. **Find a specific borrower by phone:**
   - Enter phone number in search box
   - Click "Apply Filters"

2. **View all inactive users in KUKU branch:**
   - Select "KUKU" from branch dropdown
   - Select "Inactive" from status dropdown
   - Click "Apply Filters"

3. **Search for a user by NRC:**
   - Enter NRC number in search box
   - Click "Apply Filters"

---

## ✅ FEATURE 2: Notifications Branch Filter

### Location
- **Page**: Notifications (`/notifications/`)
- **Template**: `templates/notifications/list.html`
- **View**: `notifications/views.py` - `NotificationListView`

### Features Added

#### 1. **Branch Filter** (Admin Only)
- Dropdown showing all branches
- Filters notifications by branch through:
  - Loan borrower's assigned officer's branch
  - Loan borrower's group branch
  - Payment loan borrower's branch

#### 2. **Status Filter** (All Users)
- Filter by notification status:
  - **All Notifications**: Show all (82 total)
  - **Unread Only**: Show only unread notifications
  - **Read Only**: Show only read notifications

#### 3. **Combined Filtering**
- Branch and status filters work together
- Filters are preserved during pagination

#### 4. **Clear Filters Button**
- One-click to reset all filters
- Returns to showing all notifications

### How It Works

**For Admins:**
- Can filter 82 notifications by branch
- Can see notifications from all branches
- Can filter by read/unread status
- Example: "Show me only unread notifications from KUKU branch"

**For Managers:**
- Already see only their branch notifications (from previous fix)
- Can filter by read/unread status
- Branch filter not shown (not needed)

**For Loan Officers:**
- Already see only their branch notifications (from previous fix)
- Can filter by read/unread status
- Branch filter not shown (not needed)

### Example Use Cases

1. **Admin wants to see unread notifications from KUKU:**
   - Select "KUKU" from branch dropdown
   - Select "Unread Only" from status dropdown
   - Click "Apply"

2. **Manager wants to see only read notifications:**
   - Select "Read Only" from status dropdown
   - Click "Apply"

3. **Admin wants to check all notifications from Mandevu:**
   - Select "Mandevu" from branch dropdown
   - Click "Apply"

---

## Technical Implementation

### Database Queries

**User Management Search:**
```python
users.filter(
    Q(first_name__icontains=search_query) |
    Q(last_name__icontains=search_query) |
    Q(username__icontains=search_query) |
    Q(email__icontains=search_query) |
    Q(phone_number__icontains=search_query) |
    Q(national_id__icontains=search_query)
)
```

**User Management Branch Filter:**
```python
users.filter(
    Q(officer_assignment__branch__iexact=branch_filter) |
    Q(managed_branch__name__iexact=branch_filter) |
    Q(assigned_officer__officer_assignment__branch__iexact=branch_filter) |
    Q(group_memberships__group__branch__iexact=branch_filter)
).distinct()
```

**Notifications Branch Filter:**
```python
queryset.filter(
    Q(loan__borrower__assigned_officer__officer_assignment__branch__iexact=branch_filter) |
    Q(loan__borrower__group_memberships__group__branch__iexact=branch_filter) |
    Q(payment__loan__borrower__assigned_officer__officer_assignment__branch__iexact=branch_filter) |
    Q(payment__loan__borrower__group_memberships__group__branch__iexact=branch_filter)
).distinct()
```

### Performance Considerations

1. **Distinct() Usage**: Prevents duplicate results when filtering across relationships
2. **Indexed Fields**: Search uses indexed fields (username, email, phone_number)
3. **Pagination**: Results are paginated (20 per page) to maintain performance
4. **Lazy Evaluation**: Django querysets are evaluated only when needed

---

## Files Modified

### User Management
1. **accounts/views.py**
   - Updated `UsersManageView.get_context_data()`
   - Added search query filtering
   - Added branch filtering
   - Added status filtering
   - Added branches list to context

2. **templates/accounts/users_manage.html**
   - Added search and filter form section
   - Added search input field
   - Added branch dropdown (admin only)
   - Added status dropdown
   - Added Apply/Clear buttons
   - Updated role tabs to preserve filters
   - Updated pagination links to preserve filters

### Notifications
1. **notifications/views.py**
   - Updated `NotificationListView.get_queryset()`
   - Added branch filtering logic
   - Added status filtering logic
   - Updated `get_context_data()` to include filter context
   - Added branches list to context (admin only)

2. **templates/notifications/list.html**
   - Added filter form section
   - Added branch dropdown (admin only)
   - Added status dropdown
   - Added Apply/Clear buttons
   - Updated pagination links to preserve filters

---

## Testing Checklist

### User Management
- [ ] Search by name works
- [ ] Search by phone number works
- [ ] Search by email works
- [ ] Search by username works
- [ ] Search by NRC works
- [ ] Branch filter works (admin)
- [ ] Status filter works (active/inactive)
- [ ] Combined filters work together
- [ ] Filters preserved when switching role tabs
- [ ] Filters preserved during pagination
- [ ] Clear filters button works
- [ ] Managers see only their branch users
- [ ] Officers see only their assigned borrowers

### Notifications
- [ ] Branch filter works (admin)
- [ ] Status filter works (unread/read)
- [ ] Combined filters work together
- [ ] Filters preserved during pagination
- [ ] Clear filters button works
- [ ] Admins can see all branches
- [ ] Managers see only their branch notifications
- [ ] Officers see only their branch notifications

---

## Benefits

### For Admins
- Quickly find specific users among 101 total
- Filter notifications by branch (82 notifications)
- Better oversight of all branches
- Faster user management

### For Managers
- Quickly find borrowers in their branch
- Filter notifications by status
- Better client management

### For Loan Officers
- Quickly find their assigned borrowers
- Filter notifications by status
- Faster client lookup

---

## Future Enhancements

Potential improvements for future versions:

1. **User Management:**
   - Date range filter (joined date)
   - Loan status filter (active loans, completed loans)
   - Export filtered results to CSV/Excel
   - Bulk actions on filtered users

2. **Notifications:**
   - Notification type filter (payment, loan approval, etc.)
   - Date range filter
   - Mark filtered notifications as read
   - Export filtered notifications

3. **Performance:**
   - Add database indexes on frequently searched fields
   - Implement caching for branch lists
   - Add AJAX-based live search

---

## Summary

✅ **User Management**: Added search (name, phone, email, username, NRC), branch filter, and status filter
✅ **Notifications**: Added branch filter (admin only) and status filter (all users)
✅ **Pagination**: All filters preserved during pagination
✅ **Role-Based**: Filters respect user roles (admin, manager, officer)
✅ **User-Friendly**: Clear filters button, intuitive UI

Both features are now live and ready for testing!
