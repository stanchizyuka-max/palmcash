# PythonAnywhere Deployment Guide

## Quick Deployment Steps

### 1. SSH into PythonAnywhere
```bash
ssh username@ssh.pythonanywhere.com
```

### 2. Navigate to Project Directory
```bash
cd /home/username/palmcash
```

### 3. Pull Latest Changes from GitHub
```bash
git pull origin main
```

### 4. Activate Virtual Environment
```bash
source /home/username/.virtualenvs/palmcash/bin/activate
```

### 5. Install/Update Dependencies
```bash
pip install -r requirements.txt
```

### 6. Run Database Migrations
```bash
python palmcash/manage.py migrate
```

### 7. Collect Static Files
```bash
python palmcash/manage.py collectstatic --noinput
```

### 8. Reload Web App
Go to PythonAnywhere web console and reload the web app, or use:
```bash
touch /var/www/username_pythonanywhere_com_wsgi.py
```

## Recent Changes Deployed

### Client and Document Visibility Fixes
- Auto-create `ClientVerification` on borrower registration
- Update dashboard to show clients from both direct assignment and group membership
- Fix `OfficerClientsListView` to include group members
- Fix `BorrowerListView` to include group members
- Update pending documents query to include all relevant clients
- Fix invalid `sum` filter in officer_clients_list template
- Fix passbook entries context variable name in dashboard template
- Fix payment recording URL in dashboard template

## Verification Steps

After deployment, verify the following:

1. **Dashboard Loads**: Visit `/dashboard/` and verify no errors
2. **Client Visibility**: Register a new borrower and verify they appear in loan officer dashboard
3. **Document Upload**: Upload documents and verify they appear in pending documents section
4. **Client List**: Visit `/clients/officers/<id>/clients/` and verify clients display correctly

## Troubleshooting

### If migrations fail:
```bash
python palmcash/manage.py migrate --fake-initial
```

### If static files don't load:
```bash
python palmcash/manage.py collectstatic --clear --noinput
```

### If web app won't reload:
1. Check error logs in PythonAnywhere web console
2. Verify virtual environment is activated
3. Check database connection in settings

### Common Issues:
- **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
- **Database errors**: Run migrations with `python palmcash/manage.py migrate`
- **Static files not loading**: Run `collectstatic` command

## Rollback (if needed)

If you need to rollback to previous version:
```bash
git revert HEAD
git push origin main
# Then repeat deployment steps
```

## Database Backup (Recommended before deployment)

```bash
# Backup database
python palmcash/manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json

# Restore if needed
python palmcash/manage.py loaddata backup_YYYYMMDD_HHMMSS.json
```

## Environment Variables

Ensure these are set in PythonAnywhere:
- `DEBUG=False` (production)
- `SECRET_KEY=<your-secret-key>`
- `ALLOWED_HOSTS=yourdomain.pythonanywhere.com`
- `DATABASE_URL=<your-database-url>` (if using external DB)

## Support

For issues or questions:
1. Check PythonAnywhere error logs
2. Review Django debug output
3. Check database migrations status
4. Verify all dependencies are installed
