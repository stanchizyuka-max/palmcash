# Date Filter Troubleshooting Guide

## Issue: Cannot Filter Dates in Vault

### Symptoms
- Entering dates in the date filter fields
- Clicking "Filter" button
- Results don't change or show unexpected results

---

## Diagnostic Steps

### Step 1: Run the Date Filter Test
```bash
python test_date_filter.py
```

This will test:
- If date filtering works at the database level
- Date range of your transactions
- Empty string handling
- Timezone configuration

### Step 2: Check Server Logs
After clicking "Filter" with dates, check your server logs for DEBUG messages:
```bash
# If using systemd
sudo journalctl -u palmcash -f

# If running manually
# Look at the terminal where manage.py runserver is running
```

Look for lines like:
```
Vault filters - date_from: '2026-05-01', date_to: '2026-05-07', ...
Initial queryset count: 178
After date_from filter: 50
After date_to filter: 30
```

### Step 3: Check Browser Network Tab
1. Open browser DevTools (F12)
2. Go to "Network" tab
3. Enter dates and click "Filter"
4. Look at the request URL

**Expected URL:**
```
/dashboard/vault/?date_from=2026-05-01&date_to=2026-05-07
```

**If URL is missing date parameters:**
- Form is not submitting correctly
- JavaScript might be interfering
- Browser issue

---

## Common Issues and Solutions

### Issue 1: Dates Not in URL
**Symptom**: URL doesn't contain `date_from` or `date_to` parameters

**Possible Causes**:
1. Form not submitting
2. JavaScript preventing submission
3. Browser autocomplete interfering

**Solutions**:
```html
<!-- Check if form has correct method -->
<form method="get" action="">
  <!-- Should be GET, not POST -->
</form>

<!-- Check if inputs have correct names -->
<input type="date" name="date_from" value="{{ filters.date_from }}">
<input type="date" name="date_to" value="{{ filters.date_to }}">
```

### Issue 2: Dates in URL But Not Filtering
**Symptom**: URL has dates but results don't change

**Possible Causes**:
1. Date format mismatch
2. Timezone issues
3. transaction_date field is NULL
4. Logic error in view

**Solutions**:
- Run `python test_date_filter.py` to test database queries
- Check server logs for filter counts
- Verify date format is YYYY-MM-DD

### Issue 3: Shows 0 Results When Dates Entered
**Symptom**: Entering any dates shows "No vault transactions yet"

**Possible Causes**:
1. Date range doesn't include any transactions
2. Dates are in wrong format
3. Combining with other filters that exclude everything

**Solutions**:
- Click "Clear" to reset all filters
- Check date range of your transactions:
  ```bash
  python check_vault_transactions.py
  ```
- Try a very wide date range (e.g., 2020-01-01 to 2030-12-31)

### Issue 4: Empty Dates Show 0 Results
**Symptom**: Clicking "Filter" without entering dates shows 0 results

**This should be FIXED** - empty dates should show all transactions.

**If still happening**:
1. Check if `.strip()` is being applied to date inputs
2. Verify empty strings are falsy in Python
3. Check server logs to see if empty dates are being filtered

---

## Testing Checklist

Test these scenarios:

- [ ] **No dates entered** → Click "Filter" → Should show ALL transactions
- [ ] **Only date_from** → Enter start date → Should show transactions from that date onwards
- [ ] **Only date_to** → Enter end date → Should show transactions up to that date
- [ ] **Both dates** → Enter date range → Should show transactions in that range
- [ ] **Invalid range** → date_from > date_to → Should show 0 results (correct)
- [ ] **Future dates** → Enter dates in future → Should show 0 results (correct)
- [ ] **Past dates** → Enter dates before any transactions → Should show 0 results (correct)
- [ ] **Click Clear** → Should reset to all transactions

---

## Debug Mode

### Enable Detailed Logging

The vault view now includes debug logging. To see it:

1. **Check Django settings** (`palmcash/settings.py`):
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',  # Change to DEBUG for more detail
    },
}
```

2. **Restart server** to apply logging changes

3. **Test filtering** and watch server output

### Manual SQL Test

Test the query directly in Django shell:

```python
python manage.py shell

from expenses.models import VaultTransaction
from datetime import date

# Test date filtering
qs = VaultTransaction.objects.filter(
    transaction_date__date__gte='2026-05-01',
    transaction_date__date__lte='2026-05-07'
)

print(f"Count: {qs.count()}")
print(f"SQL: {qs.query}")

# Show results
for tx in qs[:10]:
    print(f"{tx.transaction_date.date()} | {tx.branch} | {tx.transaction_type}")
```

---

## Expected Behavior

### Scenario 1: Empty Dates
```
Input: date_from = "", date_to = ""
Expected: Show ALL transactions (178 in your case)
```

### Scenario 2: Start Date Only
```
Input: date_from = "2026-05-06", date_to = ""
Expected: Show transactions from May 6 onwards
```

### Scenario 3: End Date Only
```
Input: date_from = "", date_to = "2026-05-07"
Expected: Show transactions up to May 7
```

### Scenario 4: Date Range
```
Input: date_from = "2026-05-06", date_to = "2026-05-07"
Expected: Show transactions between May 6 and May 7
```

---

## Quick Fix Attempts

### 1. Clear Browser Cache
```
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

### 2. Try Different Browser
Test in:
- Chrome
- Firefox
- Edge

### 3. Check Date Input Format
Some browsers require specific date formats. The HTML5 date input should use `YYYY-MM-DD`.

### 4. Disable Browser Extensions
Some extensions (ad blockers, form fillers) can interfere with form submission.

---

## Report Issue

If none of the above works, please provide:

1. **Test script output**:
   ```bash
   python test_date_filter.py > date_test_output.txt
   ```

2. **Server logs** when clicking Filter with dates

3. **Browser Network tab screenshot** showing the request URL

4. **What you're entering**:
   - date_from: ?
   - date_to: ?
   - Other filters: ?

5. **What you expect** vs **what you see**

---

## Files Modified

- `dashboard/vault_views.py` - Added debug logging
- `test_date_filter.py` - Date filter test script
- `DATE_FILTER_TROUBLESHOOTING.md` - This guide
