# CSRF Token Error - Solution

## Issue
Getting "CSRF verification failed" error when trying to disburse a loan.

## Root Cause
The template was cached on PythonAnywhere. After updating the template, you need to reload the web app for changes to take effect.

## Solution

### Step 1: Reload Web App on PythonAnywhere
1. Go to https://www.pythonanywhere.com/
2. Click on the **"Web"** tab
3. Find your web app (stan13.pythonanywhere.com)
4. Click the **"Reload"** button
5. Wait for it to complete (usually 10-30 seconds)

### Step 2: Clear Browser Cache
1. Press `Ctrl + Shift + Delete` (or `Cmd + Shift + Delete` on Mac)
2. Select "Cookies and other site data"
3. Click "Clear data"

### Step 3: Refresh the Page
1. Go back to the loan detail page
2. Press `Ctrl + F5` (or `Cmd + Shift + R` on Mac) to hard refresh
3. Try the disburse action again

## Why This Happens
- Django caches templates for performance
- When you update a template file, the cache isn't automatically cleared
- PythonAnywhere needs to reload the application to pick up new files
- Browser cache can also hold old versions of the page

## Prevention
After making template changes:
1. Always reload the web app on PythonAnywhere
2. Clear browser cache
3. Hard refresh the page (Ctrl+F5)

## If Problem Persists
1. Check that the csrf_token tag is in the form (it is ✓)
2. Make sure cookies are enabled in your browser
3. Try in an incognito/private window
4. Check the Django logs for more details

