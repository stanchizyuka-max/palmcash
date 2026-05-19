# Deployment Checklist - May 19, 2026

## ✅ Changes Pushed to GitHub

**Commit**: `325da94` - "Add search filters to User Management and Notifications pages"

**Repository**: https://github.com/stanchiz yuka-max/palmcash.git

---

## 🚀 Deployment Steps Required

### Step 1: Pull Changes on Server

SSH into your server and pull the latest changes:

```bash
ssh iwnd349@ipanel2
cd ~/www/palmcashloans.site
git pull origin main
```

### Step 2: Clear Python Cache

Clear all cached bytecode files:

```bash
cd ~/www/palmcashloans.site
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
```

**OR** use the provided script:

```bash
./restart_server_and_clear_cache.sh
```

### Step 3: Restart Services

Restart Gunicorn and Nginx:

```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

Verify services are running:

```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
```

### Step 4: Verify Deployment

Run the test scripts:

```bash
# Test phone validation
python verify_phone_fix.py

# Test search filters
python test_search_filters.py
```

### Step 5: Clear Browser Cache

**Important**: Users must clear their browser cache or use incognito mode to see the changes.

- Press **Ctrl + Shift + Delete**
- Select "Cached images and files"
- Click "Clear data"

---

## 📋 Features Deployed

### 1. User Management Search Filters

**Location**: `/accounts/users/manage/`

**Features**:
- ✅ Search by name, phone, email, username, NRC
- ✅ Filter by branch (admin only)
- ✅ Filter by status (active/inactive)
- ✅ Combined filtering
- ✅ Filters preserved during pagination
- ✅ Clear filters button

**Test**:
1. Go to User Management page
2. Try searching for a user by phone number
3. Try filtering by branch (if admin)
4. Try filtering by status
5. Verify pagination preserves filters

### 2. Notifications Branch Filter

**Location**: `/notifications/`

**Features**:
- ✅ Filter by branch (admin only)
- ✅ Filter by status (read/unread)
- ✅ Combined filtering
- ✅ Filters preserved during pagination
- ✅ Clear filters button

**Test**:
1. Go to Notifications page
2. Try filtering by branch (if admin)
3. Try filtering by status
4. Verify pagination preserves filters

### 3. Phone Validation Fix Documentation

**Issue**: Phone numbers starting with 05 were being rejected

**Root Cause**: Cached Python bytecode files

**Solution**: 
- Clear Python cache
- Restart server
- Clear browser cache

**Files Created**:
- `FIX_05_PHONE_NUMBERS_INSTRUCTIONS.md` - User guide
- `PHONE_VALIDATION_FIX.md` - Technical details
- `verify_phone_fix.py` - Verification script
- `restart_server_and_clear_cache.sh` - Restart script (Linux)
- `restart_server_and_clear_cache.ps1` - Restart script (Windows)

---

## 🧪 Testing Checklist

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

### Notifications
- [ ] Branch filter works (admin)
- [ ] Status filter works (unread/read)
- [ ] Combined filters work together
- [ ] Filters preserved during pagination
- [ ] Clear filters button works

### Phone Validation
- [ ] Numbers starting with 055 are accepted
- [ ] Numbers starting with 057 are accepted
- [ ] Numbers starting with 095, 096, 097 are accepted
- [ ] Numbers starting with 076, 077 are accepted
- [ ] Invalid numbers (051, 099) are rejected

---

## 📁 Files Modified

### Modified Files
1. `accounts/views.py` - Added search and filter logic
2. `notifications/views.py` - Added branch and status filter logic
3. `templates/accounts/users_manage.html` - Added search/filter UI
4. `templates/notifications/list.html` - Added filter UI

### New Files
1. `SEARCH_AND_FILTER_FEATURES.md` - Complete documentation
2. `FIX_05_PHONE_NUMBERS_INSTRUCTIONS.md` - Phone fix guide
3. `PHONE_VALIDATION_FIX.md` - Technical details
4. `restart_server_and_clear_cache.sh` - Linux restart script
5. `restart_server_and_clear_cache.ps1` - Windows restart script
6. `test_search_filters.py` - Test script for filters
7. `verify_phone_fix.py` - Phone validation test script
8. `DEPLOYMENT_CHECKLIST.md` - This file

---

## 🎯 Expected Results

### Before Deployment
- User Management: No search or filter options (hard to find users among 101)
- Notifications: No branch filter (admins see all 82 notifications mixed)
- Phone Validation: Numbers starting with 05 rejected (if cache not cleared)

### After Deployment
- User Management: Search bar + branch filter + status filter
- Notifications: Branch filter + status filter
- Phone Validation: All valid Zambian numbers accepted (055, 057, 095, 096, 097, 076, 077)

---

## ⚠️ Important Notes

1. **Server Restart Required**: Changes won't take effect until server is restarted
2. **Browser Cache**: Users must clear browser cache to see changes
3. **Python Cache**: Must be cleared before restarting server
4. **Permissions**: Branch filter only visible to admins
5. **Backward Compatible**: All existing functionality preserved

---

## 🆘 Troubleshooting

### Issue: Filters not showing
**Solution**: Clear browser cache (Ctrl+Shift+Delete) or use incognito mode

### Issue: Phone validation still rejecting 05 numbers
**Solution**: 
1. Clear Python cache: `find . -name "*.pyc" -delete`
2. Restart server: `sudo systemctl restart gunicorn`
3. Clear browser cache

### Issue: Search returns no results
**Solution**: Check if search query is correct, try partial matches

### Issue: Branch filter not showing
**Solution**: Branch filter only visible to admin users

### Issue: Server errors after deployment
**Solution**: 
1. Check server logs: `sudo journalctl -u gunicorn -n 50`
2. Verify all files pulled: `git status`
3. Check Python syntax: `python manage.py check`

---

## 📞 Support

If you encounter issues:

1. Check server logs:
   ```bash
   sudo journalctl -u gunicorn -n 50 --no-pager
   ```

2. Run test scripts:
   ```bash
   python verify_phone_fix.py
   python test_search_filters.py
   ```

3. Verify database connectivity:
   ```bash
   python manage.py dbshell
   ```

4. Check Django settings:
   ```bash
   python manage.py check --deploy
   ```

---

## ✅ Deployment Complete

Once all steps are completed and tests pass:

- ✅ Changes pulled from GitHub
- ✅ Python cache cleared
- ✅ Server restarted
- ✅ Browser cache cleared
- ✅ Features tested and working
- ✅ Users notified of new features

---

**Deployed By**: Kiro AI Assistant
**Deployment Date**: May 19, 2026
**Commit**: 325da94
**Status**: Ready for Production
