# Run Migrations on PythonAnywhere - Complete Guide

The database is missing the `manager_approval_required` column. You need to run Django migrations.

## Method 1: Using PythonAnywhere Bash Console (Recommended)

1. Log in to PythonAnywhere
2. Go to **Consoles** tab
3. Click **Bash** to open a terminal
4. Run these commands:

```bash
cd /home/stan13/palmcash/palmcash
source /home/stan13/.virtualenvs/palmcash-env/bin/activate
python manage.py migrate
```

5. You should see output like:
```
Running migrations:
  Applying loans.0010_loan_manager_approval_required_and_more... OK
  Applying loans.0011_alter_approvallog_approval_type... OK
  Applying loans.0012_alter_approvallog_approval_type... OK
```

6. Go to **Web** tab and click **Reload** to restart the app

## Method 2: Using SSH

```bash
ssh stan13@ssh.pythonanywhere.com
cd /home/stan13/palmcash/palmcash
source /home/stan13/.virtualenvs/palmcash-env/bin/activate
python manage.py migrate
```

Then reload the web app from the Web tab.

## Method 3: Manual SQL (If Django Migrations Fail)

If Django migrations fail, you can apply the schema changes manually:

1. Go to **Databases** tab on PythonAnywhere
2. Click on your database to open phpMyAdmin
3. Select your database
4. Go to **SQL** tab
5. Copy and paste the contents of `apply_migrations_manual.sql`
6. Click **Go** to execute

Then run:
```bash
python manage.py migrate --fake-initial
```

## Verify Migrations Applied

After running migrations, verify they were applied:

```bash
python manage.py showmigrations loans
```

You should see all migrations marked with `[X]`:
```
loans
 [X] 0001_initial
 [X] 0002_alter_loan_term_months_and_more
 ...
 [X] 0010_loan_manager_approval_required_and_more
 [X] 0011_alter_approvallog_approval_type
 [X] 0012_alter_approvallog_approval_type
```

## Troubleshooting

### Error: "Table already exists"
This means the migration was partially applied. Run:
```bash
python manage.py migrate --fake loans 0009_approvallog
python manage.py migrate
```

### Error: "Database is locked"
Wait a few minutes and try again. The database may be processing another operation.

### Error: "Permission denied"
Ensure you're using the correct virtual environment:
```bash
which python
# Should show: /home/stan13/.virtualenvs/palmcash-env/bin/python
```

### Migrations still not running after reload
Check the error log:
1. Go to **Web** tab
2. Click on your web app
3. Scroll down to **Log files**
4. Click on **Error log** to see what went wrong

## After Migrations

1. The app should work without the `manager_approval_required` error
2. The manager loan approval workflow will be fully functional
3. All new features will be available

## Quick Reference

```bash
# Activate virtual environment
source /home/stan13/.virtualenvs/palmcash-env/bin/activate

# Run migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations

# Reload web app
# (Do this from PythonAnywhere Web tab)
```
