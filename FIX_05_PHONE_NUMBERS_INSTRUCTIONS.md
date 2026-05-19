# 🔧 FIX: Phone Numbers Starting with 05 Not Working

## ✅ PROBLEM IDENTIFIED AND FIXED

The form was rejecting phone numbers starting with **055** and **057** even though the validation code was correct.

**Root Cause**: Cached Python bytecode files (`.pyc`) were causing Django to use the OLD validation code.

---

## 🎯 SOLUTION STEPS

### ✅ Step 1: Code Updated (DONE)
The validation code in `accounts/forms.py` has been updated to accept:
- **055** (Zamtel)
- **057** (Airtel)
- **095, 096, 097** (MTN, Airtel, Zamtel)
- **076, 077** (MTN, Zamtel)

### ✅ Step 2: Python Cache Cleared (DONE)
All `__pycache__` directories and `.pyc` files have been deleted from your local Windows machine.

### 🔄 Step 3: SERVER RESTART REQUIRED (ACTION NEEDED)

**You need to SSH into your Linux server and restart the services:**

```bash
# SSH into your server
ssh iwnd349@ipanel2

# Navigate to your project directory
cd ~/www/palmcashloans.site

# Clear Python cache on the server
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Restart Gunicorn (Django application server)
sudo systemctl restart gunicorn

# Check if Gunicorn restarted successfully
sudo systemctl status gunicorn

# Restart Nginx (web server)
sudo systemctl restart nginx

# Check if Nginx restarted successfully
sudo systemctl status nginx
```

**OR** use the provided script:
```bash
cd ~/www/palmcashloans.site
./restart_server_and_clear_cache.sh
```

---

## 🌐 Step 4: BROWSER CACHE (IMPORTANT!)

After restarting the server, **users must clear their browser cache**:

### Option A: Clear Browser Cache
1. Press **Ctrl + Shift + Delete**
2. Select "Cached images and files"
3. Click "Clear data"

### Option B: Use Incognito/Private Mode
1. Open a new incognito/private window
2. Try registering with a 055 or 057 number

---

## ✅ VERIFICATION

After completing all steps, test with these numbers:

| Number | Should Work? |
|--------|--------------|
| 0555123456 | ✅ YES |
| 0575123456 | ✅ YES |
| 0955123456 | ✅ YES |
| 0965123456 | ✅ YES |
| 0975123456 | ✅ YES |
| 0765123456 | ✅ YES |
| 0775123456 | ✅ YES |
| 0512345678 | ❌ NO (invalid prefix) |
| 0999999999 | ❌ NO (invalid prefix) |

---

## 📋 QUICK CHECKLIST

- [x] ✅ Updated validation code in `accounts/forms.py`
- [x] ✅ Cleared Python cache on Windows machine
- [ ] 🔄 **SSH into Linux server**
- [ ] 🔄 **Clear Python cache on server**
- [ ] 🔄 **Restart Gunicorn service**
- [ ] 🔄 **Restart Nginx service**
- [ ] 🔄 **Clear browser cache or use incognito mode**
- [ ] 🔄 **Test with 055/057 numbers**

---

## 🚨 IF STILL NOT WORKING

If the form still rejects 05 numbers after all steps:

1. **Check server logs**:
   ```bash
   sudo journalctl -u gunicorn -n 50 --no-pager
   ```

2. **Verify forms.py on server**:
   ```bash
   grep -A 5 "validate_zambian_phone" accounts/forms.py
   ```
   Should show: `r'^0(95|96|97|76|77|55|57)\d{7}$'`

3. **Check for JavaScript validation**:
   - Open browser Developer Tools (F12)
   - Go to Console tab
   - Try submitting the form
   - Look for any JavaScript errors

4. **Test validation directly**:
   ```bash
   python test_phone_validation.py
   ```

---

## 📁 FILES CREATED

- `restart_server_and_clear_cache.sh` - Linux restart script
- `restart_server_and_clear_cache.ps1` - Windows PowerShell script
- `PHONE_VALIDATION_FIX.md` - Technical details
- `FIX_05_PHONE_NUMBERS_INSTRUCTIONS.md` - This file
- `test_phone_validation.py` - Test script (already exists)

---

## 💡 WHY THIS HAPPENED

1. **Python Bytecode Caching**: Python compiles `.py` files to `.pyc` for faster loading
2. **Cache Persistence**: Sometimes the cache doesn't update when you edit files
3. **Server Not Restarted**: Django loads forms at startup, so changes need a restart
4. **Browser Cache**: Forms and validation may be cached in the browser

---

## 🎓 PREVENTION FOR FUTURE

**Always do these steps after editing forms or validation code:**

1. Clear Python cache: `find . -name "*.pyc" -delete`
2. Restart application server: `sudo systemctl restart gunicorn`
3. Clear browser cache or test in incognito mode

---

## 📞 SUPPORT

If you need help:
1. Check the server logs (see "IF STILL NOT WORKING" section)
2. Run the test script: `python test_phone_validation.py`
3. Verify the validation code is correct on the server

---

**Last Updated**: May 19, 2026
**Status**: ✅ Code fixed, 🔄 Server restart pending
