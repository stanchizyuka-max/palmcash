# Apply Migrations on PythonAnywhere

The manager loan approval workflow requires database migrations to be applied. Follow these steps:

## Option 1: Using PythonAnywhere Web Console (Recommended)

1. Go to PythonAnywhere dashboard
2. Click on "Web" tab
3. Click on "Reload" button to restart the app (this will apply pending migrations if auto-migration is enabled)

## Option 2: Using PythonAnywhere Bash Console

1. Go to PythonAnywhere dashboard
2. Click on "Consoles" tab
3. Click on "Bash" to open a terminal
4. Run these commands:

```bash
cd /home/stan13/palmcash/palmcash
source /home/stan13/.virtualenvs/palmcash-env/bin/activate
python manage.py migrate
```

## Option 3: Using SSH (if enabled)

```bash
ssh stan13@ssh.pythonanywhere.com
cd /home/stan13/palmcash/palmcash
source /home/stan13/.virtualenvs/palmcash-env/bin/activate
python manage.py migrate
```

## Migrations to Apply

The following migrations need to be applied:
- `0010_loan_manager_approval_required_and_more.py` - Adds manager approval fields and ManagerLoanApproval model
- `0011_alter_approvallog_approval_type.py` - Updates ApprovalLog approval types
- `0012_alter_approvallog_approval_type.py` - Further updates to ApprovalLog

## Verify Migrations

After applying migrations, verify they were successful:

```bash
python manage.py showmigrations loans
```

You should see all migrations marked with an [X] indicating they've been applied.

## Troubleshooting

If you get an error about the database being locked:
1. Wait a few minutes for any running processes to complete
2. Try again

If migrations still fail:
1. Check the error message carefully
2. Ensure the database user has ALTER TABLE permissions
3. Contact PythonAnywhere support if needed
