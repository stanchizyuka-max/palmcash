# Deploy Payment Number Validation Fix

## Issue
ValidationError when making payments: `payment_number: This field cannot be blank`

## Fix Applied
Modified `payments/models.py` to generate `payment_number` BEFORE validation runs.

## Deployment Steps

Run these commands on the server:

```bash
# Navigate to project directory
cd ~/www/palmcashloans.site

# Pull latest changes from GitHub
git pull origin main

# Clear Python cache
find . -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Restart the server
sudo systemctl restart gunicorn

# Check server status
sudo systemctl status gunicorn
```

## Verification
After deployment, try creating a payment at `/payments/make/93/` - it should work without the validation error.

## Technical Details
**Before:** `full_clean()` was called before `payment_number` was generated, causing validation to fail.

**After:** `payment_number` is generated first, then `full_clean()` validates all fields including the now-populated payment_number.
