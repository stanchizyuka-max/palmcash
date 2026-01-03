# PythonAnywhere Deployment Checklist

Use this checklist to ensure successful deployment of Palm Cash to PythonAnywhere.

## Pre-Deployment

- [ ] Code is committed to GitHub
- [ ] `.env` file is NOT in git (check `.gitignore`)
- [ ] All tests pass locally
- [ ] `DEBUG=False` ready for production
- [ ] `SECRET_KEY` is unique and strong
- [ ] Email credentials are app-specific passwords

## PythonAnywhere Account Setup

- [ ] PythonAnywhere account created
- [ ] Email verified
- [ ] Username chosen (becomes your domain)
- [ ] Plan selected (free or paid)

## Repository Setup

- [ ] Code pushed to GitHub
- [ ] GitHub repository is accessible
- [ ] Repository URL ready

## On PythonAnywhere - Bash Console

- [ ] Repository cloned: `git clone https://github.com/yourusername/palmcash.git`
- [ ] Virtual environment created: `mkvirtualenv --python=/usr/bin/python3.11 palmcash-env`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file created with correct values
- [ ] Migrations run: `python manage.py migrate`
- [ ] Superuser created: `python manage.py createsuperuser`
- [ ] Static files collected: `python manage.py collectstatic --noinput`

## Database Setup

- [ ] MySQL database created in Databases tab
- [ ] Database name: `username$palmcash_db`
- [ ] Database password saved
- [ ] Database credentials in `.env`

## Web App Configuration

- [ ] Web app created (Manual configuration, Python 3.11)
- [ ] WSGI file configured with correct path
- [ ] Virtual environment path set: `/home/username/.virtualenvs/palmcash-env`
- [ ] Static files mapping added:
  - [ ] `/static/` → `/home/username/palmcash/staticfiles`
  - [ ] `/media/` → `/home/username/palmcash/media`
- [ ] Web app reloaded

## Verification

- [ ] Site accessible: https://username.pythonanywhere.com/
- [ ] Admin panel works: https://username.pythonanywhere.com/admin/
- [ ] Dashboard accessible: https://username.pythonanywhere.com/dashboard/
- [ ] Can login with superuser
- [ ] Static files load (CSS, JavaScript, images)
- [ ] No 404 errors for static files
- [ ] No 500 errors in error log

## Security

- [ ] `DEBUG=False` in `.env`
- [ ] `SECRET_KEY` is unique
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] HTTPS enabled (Force HTTPS)
- [ ] Database password is strong
- [ ] `.env` file permissions are secure
- [ ] No sensitive data in error logs

## Email Configuration (Optional)

- [ ] Gmail app password generated
- [ ] `EMAIL_HOST_USER` set in `.env`
- [ ] `EMAIL_HOST_PASSWORD` set in `.env`
- [ ] Test email sending works

## Monitoring

- [ ] Error log checked for issues
- [ ] Access log reviewed
- [ ] CPU usage monitored
- [ ] Database performance checked

## Backup & Maintenance

- [ ] Database backup created
- [ ] Files backup created
- [ ] Backup location noted
- [ ] Update schedule planned

## Post-Deployment

- [ ] Document your domain name
- [ ] Save database credentials securely
- [ ] Set up monitoring alerts
- [ ] Plan regular backups
- [ ] Document any custom configurations

## Troubleshooting Checklist

If something doesn't work:

- [ ] Check error log in Web tab
- [ ] Verify `.env` file exists and has correct values
- [ ] Verify virtual environment path is correct
- [ ] Verify static files mapping is correct
- [ ] Reload web app
- [ ] Check database connection
- [ ] Verify migrations ran successfully
- [ ] Check WSGI file configuration

## Quick Commands Reference

```bash
# Activate environment
workon palmcash-env

# Navigate to project
cd ~/palmcash

# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Access Django shell
python manage.py shell

# Deactivate environment
deactivate
```

## Important Paths

- **Project**: `/home/username/palmcash`
- **Virtual Env**: `/home/username/.virtualenvs/palmcash-env`
- **Static Files**: `/home/username/palmcash/staticfiles`
- **Media Files**: `/home/username/palmcash/media`
- **Database**: `username.mysql.pythonanywhere-services.com`

## Important URLs

- **Site**: `https://username.pythonanywhere.com`
- **Admin**: `https://username.pythonanywhere.com/admin`
- **Dashboard**: `https://username.pythonanywhere.com/dashboard`
- **PythonAnywhere Dashboard**: `https://www.pythonanywhere.com/user/username/`

## Credentials to Save

- [ ] PythonAnywhere username: _______________
- [ ] PythonAnywhere password: _______________
- [ ] Database password: _______________
- [ ] Superuser username: _______________
- [ ] Superuser password: _______________
- [ ] Domain name: _______________

## Support Resources

- PythonAnywhere Help: https://help.pythonanywhere.com/
- Django Docs: https://docs.djangoproject.com/
- Palm Cash Docs: See DEPLOY_PYTHONANYWHERE.md

## Deployment Status

- [ ] **Deployment Date**: _______________
- [ ] **Deployed By**: _______________
- [ ] **Status**: ✅ Live / ⚠️ Issues / ❌ Failed
- [ ] **Notes**: _______________

---

**Congratulations!** Your Palm Cash is deployed on PythonAnywhere! 🚀
