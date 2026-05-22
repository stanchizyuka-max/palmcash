# 🔧 Fix Migration Error - Quick Solution

## Problem
The migration `0999_add_audit_timestamps.py` references a parent migration that doesn't exist on your server.

## Quick Fix (Option 1 - Recommended)

### Step 1: Add Columns Directly via SQL
```bash
# On production server
cd ~/www/palmcashloans.site

# Connect to MySQL
mysql -u your_db_user -p your_db_name

# Run these SQL commands:
ALTER TABLE loans_loan 
ADD COLUMN approval_recorded_at DATETIME(6) NULL 
COMMENT 'System timestamp: when approval was recorded in the system';

ALTER TABLE loans_loan 
ADD COLUMN disbursement_recorded_at DATETIME(6) NULL 
COMMENT 'System timestamp: when disbursement was recorded in the system';

# Verify columns were added
DESCRIBE loans_loan;

# Exit MySQL
exit;
```

### Step 2: Delete the Problematic Migration
```bash
rm loans/migrations/0999_add_audit_timestamps.py
```

### Step 3: Create a Fake Migration Record
```bash
python manage.py shell
```

```python
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

recorder = MigrationRecorder(connection)
recorder.record_applied('loans', '0999_add_audit_timestamps')
exit()
```

### Step 4: Run the Fix Script
```bash
python manage.py fix_backdated_loans --dry-run
```

If that works, run:
```bash
python manage.py fix_backdated_loans
```

### Step 5: Restart Server
```bash
sudo systemctl restart gunicorn
```

---

## Alternative Fix (Option 2 - If Option 1 Fails)

### Use the SQL File
```bash
# On production server
cd ~/www/palmcashloans.site

# Run the SQL script
mysql -u your_db_user -p your_db_name < add_audit_columns.sql
```

Then follow steps 2-5 from Option 1.

---

## Alternative Fix (Option 3 - Create Proper Migration)

### Step 1: Find Latest Migration
```bash
cd ~/www/palmcashloans.site
ls -1 loans/migrations/*.py | grep -v __pycache__ | grep -v __init__ | tail -5
```

**Example output:**
```
loans/migrations/0094_something.py
loans/migrations/0095_something_else.py
loans/migrations/0096_another_thing.py
loans/migrations/0097_final_thing.py
loans/migrations/0999_add_audit_timestamps.py
```

### Step 2: Rename Migration
```bash
# If latest is 0097, rename to 0098
mv loans/migrations/0999_add_audit_timestamps.py loans/migrations/0098_add_audit_timestamps.py
```

### Step 3: Edit Migration File
```bash
nano loans/migrations/0098_add_audit_timestamps.py
```

Change the dependencies line to match your latest migration:
```python
dependencies = [
    ('loans', '0097_final_thing'),  # Change this to YOUR latest migration
]
```

### Step 4: Run Migration
```bash
python manage.py migrate loans
```

### Step 5: Run Fix Script
```bash
python manage.py fix_backdated_loans --dry-run
python manage.py fix_backdated_loans
```

### Step 6: Restart Server
```bash
sudo systemctl restart gunicorn
```

---

## Verification

After applying the fix, verify the columns exist:

```bash
python manage.py dbshell
```

```sql
DESCRIBE loans_loan;
```

You should see:
```
approval_recorded_at    | datetime(6) | YES  |     | NULL    |
disbursement_recorded_at| datetime(6) | YES  |     | NULL    |
```

---

## Which Option Should I Use?

- **Option 1** (SQL + Fake Migration): Fastest, works immediately
- **Option 2** (SQL File): Same as Option 1, but uses the SQL file
- **Option 3** (Proper Migration): Most "correct" but requires finding migration numbers

**Recommendation**: Use **Option 1** - it's the fastest and safest.

---

## After Fix is Applied

Once columns are added and fix script runs successfully:

```bash
# Restart server
sudo systemctl restart gunicorn

# Check website
curl -I https://palmcashloans.site

# Monitor logs
sudo journalctl -u gunicorn -f
```

---

**Created**: May 22, 2026  
**Status**: Ready to Apply
