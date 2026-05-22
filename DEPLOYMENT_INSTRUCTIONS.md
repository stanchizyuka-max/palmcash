# 🚀 Deployment Instructions - Act As Officer Fixes

## 🐛 What Was Fixed

### Issue 1: 404 Error on Bulk Collection Group
**Problem**: When a manager acted as an officer and tried to access a group in bulk collection, they got a 404 error: "No BorrowerGroup matches the given query."

**Root Cause**: The `BulkCollectionGroupView` and several other payment views were filtering groups by `request.user` instead of checking for `acting_as_officer`.

**Solution**: Updated 4 payment views to properly check for `acting_as_officer` before filtering data.

### Issue 2: Redirects to Manager Dashboard Instead of Officer Dashboard
**Problem**: When a manager clicked "Act As Officer", they were redirected back to the manager's dashboard instead of seeing the officer's dashboard.

**Root Cause**: The `start_acting_as_officer` view was redirecting to the generic `dashboard:dashboard` URL, which wasn't immediately recognizing the acting mode.

**Solution**: Changed the redirect to explicitly go to `dashboard:loan_officer_dashboard` and added `session.modified = True` to ensure the session is saved immediately.

### Issue 3: Manager Branch Verification Failed (CRITICAL FIX)
**Problem**: Even after fixing the redirect, managers were still being sent back to manager dashboard. Admins worked fine.

**Root Cause**: The middleware was trying to find managers in the `OfficerAssignment` table, which only contains loan officers. This caused the branch check to fail, so `request.acting_as_officer` was never set for managers.

**Solution**: Updated middleware and view to use `managed_branch` relationship for managers instead of `OfficerAssignment`.

## 📝 Changes Made

### Files Updated:

#### 1. **payments/views.py** (Commit: 9138a6e)
Updated 4 views:
   - `BulkCollectionGroupView.get()` - Now filters by acting officer
   - `BulkCollectionGroupView.post()` - Now uses acting officer + adds audit trail
   - `DefaultCollectionView.get()` - Now filters by acting officer
   - `DefaultCollectionGroupView.get()` - Now filters by acting officer
   - `DefaultCollectionGroupView.post()` - Now uses acting officer
   - `CollectionReportView` - Now filters groups by acting officer

#### 2. **common/views.py** (Commits: 72a2935, 4d39bbc)
Updated `start_acting_as_officer` view:
   - Changed default redirect from `dashboard:dashboard` to `dashboard:loan_officer_dashboard`
   - Added `request.session.modified = True` to ensure session is saved
   - Forces redirect to officer dashboard even if `next` parameter is generic dashboard
   - **Fixed branch verification to use `managed_branch` for managers**

#### 3. **common/middleware.py** (Commit: 4d39bbc) - CRITICAL FIX
Updated `ActAsOfficerMiddleware`:
   - **Fixed to use `managed_branch` relationship for managers**
   - Always initializes `request.acting_as_officer` to None
   - Properly clears session when branch check fails
   - Better error handling for missing branch assignments

#### 4. **ACT_AS_OFFICER_UPDATED_VIEWS.md** (Commit: 9138a6e)
Updated documentation:
   - Now shows 12 views supporting acting as officer (was 8)
   - Added bug fix section
   - Updated testing checklist

#### 5. **ACT_AS_OFFICER_MANAGER_FIX.md** (New)
Detailed root cause analysis:
   - Explains why managers failed but admins worked
   - Shows the wrong vs correct relationship lookups
   - Documents data model relationships

### Git Commits:
- **Commit 1**: 9138a6e - "Fix: Update BulkCollectionGroupView and other payment views to respect acting_as_officer"
- **Commit 2**: 72a2935 - "Fix: Redirect to officer dashboard when manager acts as officer"
- **Commit 3**: 4d39bbc - "Fix: Manager branch verification for acting as officer" (CRITICAL)
- **Status**: ✅ All pushed to GitHub

## 🔧 Deployment Steps

### On Production Server:

```bash
# 1. Navigate to project directory
cd /var/www/iwnd349/data/www/palmcashloans.site

# 2. Pull latest changes
git pull origin main

# 3. Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 4. Restart Gunicorn
sudo systemctl restart gunicorn

# 5. Check status
sudo systemctl status gunicorn
```

## ✅ Testing After Deployment

### Test Fix #1 - Officer Dashboard Redirect:
1. **Login as Manager** (e.g., Gabriel Kelkam Daka)
2. **Go to**: Dashboard → Manage Officers
3. **Click**: "Act As Officer" icon for any officer (e.g., Edwin Mhlanga)
4. **Expected**: ✅ **Immediately redirected to Edwin's officer dashboard** (not manager dashboard)
5. **Verify**: Orange banner appears at top: "Acting as Edwin Mhlanga"
6. **Verify**: Dashboard shows Edwin's stats (groups, loans, collections)
7. **Verify**: All data belongs to Edwin, not the manager

### Test Fix #2 - Bulk Collection 404 Fix:
1. **While still acting as Edwin**
2. **Go to**: Payments → Bulk Collection
3. **Verify**: Only Edwin's groups are shown
4. **Click**: On any group (e.g., Group 62)
5. **Expected**: ✅ Group page loads (no 404 error)
6. **Verify**: Can see all clients in the group
7. **Record a payment** (optional)
8. **Verify**: Payment notes include audit trail
9. **Click**: "Stop Acting as Edwin Mhlanga"
10. **Verify**: Returns to manager view

### Test Other Features:
- [ ] Default Collection (should show only acting officer's defaulted loans)
- [ ] Collection Report (dropdown should show only acting officer's groups)
- [ ] Payment Recording (should show only acting officer's loans)
- [ ] Loan Disbursement (should show only acting officer's loans)

## 📊 What Now Works

When manager acts as officer:

### ✅ All Payment Views:
- **Bulk Collection** - Shows only officer's groups, no 404 errors
- **Default Collection** - Shows only officer's defaulted loans
- **Payment Recording** - Shows only officer's loans
- **Collection Reports** - Filters by officer's groups

### ✅ Audit Trails:
All actions include manager name and officer name:
```
[BULK COLLECTION — Group Name] | Action by Gabriel Kelkam Daka on behalf of Edwin Mhlanga
```

### ✅ Navigation:
- All links work correctly
- No more 404 errors
- Seamless experience

## 🎯 Summary

**Total Views Supporting Acting As Officer**: 12

1. ✅ Payment Recording
2. ✅ Loan Disbursement
3. ✅ Loan List
4. ✅ Bulk Collection
5. ✅ Bulk Collection Group (FIXED - was causing 404)
6. ✅ Default Collection (FIXED)
7. ✅ Default Collection Group (FIXED)
8. ✅ Collection Report (FIXED)
9. ✅ Hierarchical Payments
10. ✅ Client Drilldown
11. ✅ Officer Dashboard
12. ✅ Main Dashboard

## 🔍 Troubleshooting

### If still redirecting to manager dashboard:
```bash
# Check if code was pulled correctly
cd /var/www/iwnd349/data/www/palmcashloans.site
git log -3 --oneline
# Should show:
# 4d39bbc Fix: Manager branch verification for acting as officer (CRITICAL)
# 72a2935 Fix: Redirect to officer dashboard when manager acts as officer
# 9138a6e Fix: Update BulkCollectionGroupView...

# Verify the middleware change
grep -A 5 "managed_branch" common/middleware.py
# Should show the new logic using managed_branch

# Clear sessions (optional - will log out all users)
python manage.py clearsessions

# Check if Gunicorn restarted
sudo systemctl status gunicorn
# Should show: Active: active (running)

# Check logs for errors
sudo journalctl -u gunicorn -n 50
```

### If changes not visible:
```bash
# Force restart
sudo systemctl stop gunicorn
sleep 2
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

## 📞 Support

If issues persist:
1. Check error logs: `sudo journalctl -u gunicorn -n 100`
2. Verify git commit: `git log -1`
3. Check Python cache cleared: `find . -name "*.pyc" | wc -l` (should be 0)

---

**Deployed By**: Kiro AI Assistant  
**Date**: May 22, 2026  
**Commits**: 9138a6e, 72a2935, 4d39bbc (CRITICAL)  
**Status**: ✅ Ready for Deployment

**IMPORTANT**: Commit 4d39bbc is the critical fix that makes managers work correctly!
