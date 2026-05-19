# Phone Validation Fix - Numbers Starting with 05

## Problem
Form was rejecting phone numbers starting with 055 and 057 despite the validation code being updated.

## Root Cause
**Cached Python bytecode files** in `accounts/__pycache__/` were causing Django to use the old validation code even though `accounts/forms.py` had been updated.

## Solution Applied

### 1. ✅ Updated Validation Code (Already Done)
File: `accounts/forms.py`
- Updated `validate_zambian_phone()` function to accept 055 and 057 prefixes
- Pattern: `r'^0(95|96|97|76|77|55|57)\d{7}$'`
- Accepts: 055, 057, 095, 096, 097, 076, 077

### 2. ✅ Cleared Python Cache
- Deleted `accounts/__pycache__/` directory
- This forces Python to recompile forms.py with the new validation

### 3. 🔄 Server Restart Required
Run the restart script:
```bash
./restart_server_and_clear_cache.sh
```

Or manually:
```bash
# Clear all Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Restart Gunicorn
sudo systemctl restart gunicorn

# Restart Nginx (optional but recommended)
sudo systemctl restart nginx
```

### 4. 🌐 Browser Cache
After server restart, users must:
1. Clear browser cache (Ctrl+Shift+Delete)
2. Or use incognito/private browsing mode
3. Try registering with 055 or 057 numbers

## Verification
Run the test script to confirm validation works:
```bash
python test_phone_validation.py
```

Expected output:
```
✅ 0555123456 - ACCEPTED
✅ 0575123456 - ACCEPTED
✅ 0955123456 - ACCEPTED
✅ 0965123456 - ACCEPTED
✅ 0975123456 - ACCEPTED
✅ 0765123456 - ACCEPTED
✅ 0775123456 - ACCEPTED
```

## Why This Happened
1. **Python Bytecode Caching**: Python compiles `.py` files to `.pyc` bytecode for faster loading
2. **Cache Not Invalidated**: When you edit a `.py` file, Python should recompile, but sometimes the cache persists
3. **Server Not Restarted**: Django loads forms.py at startup, so changes require a server restart
4. **Browser Cache**: Forms may also be cached in the browser

## Prevention
Always do these steps after editing forms or validation code:
1. Clear Python cache: `find . -name "*.pyc" -delete`
2. Restart the application server
3. Clear browser cache or test in incognito mode

## Files Modified
- `accounts/forms.py` - Updated validation patterns
- `accounts/__pycache__/` - Deleted (will be regenerated)
- `restart_server_and_clear_cache.sh` - Created for easy restarts
- `test_phone_validation.py` - Test script (already exists)

## Status
- ✅ Code updated
- ✅ Cache cleared
- 🔄 **ACTION REQUIRED**: Run `./restart_server_and_clear_cache.sh`
- 🔄 **ACTION REQUIRED**: Clear browser cache or use incognito mode
