# How to Reload Your Web App on PythonAnywhere

The template syntax error has been fixed and pushed to GitHub. Now you need to reload your web app on PythonAnywhere to clear the cache and apply the changes.

## Option 1: Using the Web Interface (Easiest)

1. Go to https://www.pythonanywhere.com
2. Log in with your account (stan13)
3. Click on the **Web** tab at the top
4. Find your web app in the list (should be something like "stan13.pythonanywhere.com")
5. Click the green **Reload** button on the right side
6. Wait for it to complete (usually takes 10-30 seconds)
7. Visit your site to verify the fix

## Option 2: Using the Command Line

If you have SSH access (which may not work on PythonAnywhere), you can:

```bash
touch /var/www/stan13_pythonanywhere_com_wsgi.py
```

This touches the WSGI file which triggers a reload.

## Option 3: Pull Changes and Reload

1. Log into PythonAnywhere console
2. Navigate to your project:
   ```bash
   cd ~/palmcash/palmcash
   ```
3. Pull the latest changes:
   ```bash
   git pull
   ```
4. Go back to the Web tab and click Reload

## What Was Fixed

The borrower dashboard template had a Django template syntax error on line 498:

**Before (Invalid):**
```django
{{ loan.loan_type.name if loan.loan_type else 'Loan' }}
```

**After (Fixed):**
```django
{% if loan.loan_type %}
    {{ loan.loan_type.name }}
{% else %}
    Loan
{% endif %}
```

Django templates don't support inline ternary operators. You must use `{% if %}...{% else %}...{% endif %}` blocks instead.

## Verify the Fix

After reloading:
1. Visit https://stan13.pythonanywhere.com/dashboard/
2. The page should load without the TemplateSyntaxError
3. You should see the "Upfront Payments Required" section if there are any loans awaiting upfront payment

## If It Still Doesn't Work

1. Check the error log: https://www.pythonanywhere.com/user/stan13/files/var/log/
2. Look for `error.log` or `access.log`
3. Search for "TemplateSyntaxError" to see if there are other issues
4. If you see other ternary operators, they need to be fixed the same way

