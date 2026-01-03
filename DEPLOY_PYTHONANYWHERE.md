# Deploying Palm Cash to PythonAnywhere

Complete guide to deploy Palm Cash on PythonAnywhere hosting platform.

## Prerequisites

- PythonAnywhere account (free or paid)
- GitHub account with Palm Cash repository
- Domain name (optional, PythonAnywhere provides free subdomain)
- 30-45 minutes for complete deployment

## Step 1: Create PythonAnywhere Account

1. Go to https://www.pythonanywhere.com/
2. Click "Sign up"
3. Choose a plan:
   - **Free**: Good for testing/development
   - **Paid**: Recommended for production
4. Create account with username (this becomes your domain: `username.pythonanywhere.com`)
5. Verify email

## Step 2: Set Up Git Repository

Before deploying, ensure your code is on GitHub:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Palm Cash"

# Add remote (replace with your GitHub URL)
git remote add origin https://github.com/yourusername/palmcash.git

# Push to GitHub
git push -u origin main
```

## Step 3: Clone Repository on PythonAnywhere

1. Log in to PythonAnywhere
2. Open **Bash console** (from dashboard)
3. Run these commands:

```bash
# Clone your repository
git clone https://github.com/yourusername/palmcash.git
cd palmcash

# Create virtual environment (use Python 3.11)
mkvirtualenv --python=/usr/bin/python3.11 palmcash-env

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Configure Database

### 4.1 Create MySQL Database

1. Go to **Databases** tab in PythonAnywhere
2. Click **Create a new database**
3. Choose MySQL
4. Set database name: `username$palmcash_db`
5. Set password (save this!)
6. Click **Create**

### 4.2 Create .env File

In PythonAnywhere bash console:

```bash
# Navigate to project
cd ~/palmcash

# Create .env file
nano .env
```

Add this content (replace with your values):

```env
# Database Configuration
DB_NAME=username$palmcash_db
DB_USER=username
DB_PASSWORD=your_mysql_password
DB_HOST=username.mysql.pythonanywhere-services.com
DB_PORT=3306

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Django Settings
DEBUG=False
SECRET_KEY=your-very-secret-key-here-change-this
ALLOWED_HOSTS=username.pythonanywhere.com,www.username.pythonanywhere.com

# Site URL
SITE_URL=https://username.pythonanywhere.com

# Currency
CURRENCY_CODE=ZMW
CURRENCY_SYMBOL=K

# Loan Settings
LOAN_INTEREST_RATE_DEFAULT=15.0
LOAN_PENALTY_RATE_DEFAULT=2.0
LOAN_GRACE_PERIOD_DAYS=7
LOAN_UPFRONT_PAYMENT_PERCENTAGE=10.0
```

Save: `Ctrl+X`, then `Y`, then `Enter`

## Step 5: Run Migrations

In bash console:

```bash
# Activate virtual environment
workon palmcash-env

# Navigate to project
cd ~/palmcash

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Follow prompts to create admin account

# Collect static files
python manage.py collectstatic --noinput
```

## Step 6: Configure Web App

1. Go to **Web** tab in PythonAnywhere
2. Click **Add a new web app**
3. Choose **Manual configuration**
4. Select **Python 3.11**
5. Click **Next**

### 6.1 Configure WSGI File

1. In Web tab, click on the WSGI configuration file link
2. Replace the content with:

```python
import os
import sys

# Add project to path
path = '/home/username/palmcash'
if path not in sys.path:
    sys.path.append(path)

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'palmcash.settings'

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(path, '.env'))

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Save the file.

### 6.2 Configure Virtual Environment

1. In Web tab, scroll to **Virtualenv** section
2. Enter path: `/home/username/.virtualenvs/palmcash-env`
3. Click the checkmark to confirm

### 6.3 Configure Static Files

1. In Web tab, scroll to **Static files** section
2. Add mapping:
   - URL: `/static/`
   - Directory: `/home/username/palmcash/staticfiles`
3. Add another mapping:
   - URL: `/media/`
   - Directory: `/home/username/palmcash/media`

## Step 7: Reload Web App

1. In Web tab, click **Reload** button
2. Wait 10-20 seconds for app to start
3. Visit your site: `https://username.pythonanywhere.com`

## Step 8: Verify Deployment

Check these URLs:

- **Main site**: https://username.pythonanywhere.com/
- **Admin panel**: https://username.pythonanywhere.com/admin/
- **Dashboard**: https://username.pythonanywhere.com/dashboard/

Login with superuser credentials created in Step 5.

## Step 9: Configure Email (Optional)

For email notifications to work:

1. Use Gmail App Password (recommended)
2. Generate at: https://myaccount.google.com/apppasswords
3. Update `.env` with:
   ```env
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```
4. Reload web app

## Step 10: Set Up SSL Certificate

PythonAnywhere provides free SSL:

1. Go to **Web** tab
2. Scroll to **Security** section
3. Click **Force HTTPS** (if available on your plan)
4. This redirects all HTTP to HTTPS

## Troubleshooting

### "ModuleNotFoundError: No module named 'django'"

**Solution:**
1. Check virtual environment path in Web tab
2. Verify path: `/home/username/.virtualenvs/palmcash-env`
3. Reload web app

### "Static files not found (404)"

**Solution:**
1. Run: `python manage.py collectstatic --noinput`
2. Verify static files mapping in Web tab
3. Reload web app

### "Database connection refused"

**Solution:**
1. Check database credentials in `.env`
2. Verify database exists in Databases tab
3. Check `.env` file is in correct location
4. Reload web app

### "Internal Server Error (500)"

**Solution:**
1. Check error log in Web tab → Error log
2. Verify `.env` file exists and has correct values
3. Check migrations ran successfully
4. Reload web app

### "DEBUG=False shows blank page"

**Solution:**
1. Check error log for actual error
2. Temporarily set `DEBUG=True` to see error
3. Fix the issue
4. Set `DEBUG=False` again

## Updating Your Application

When you make changes locally:

```bash
# Commit and push to GitHub
git add .
git commit -m "Your changes"
git push origin main

# On PythonAnywhere bash console:
cd ~/palmcash
git pull origin main

# Activate environment
workon palmcash-env

# Install any new dependencies
pip install -r requirements.txt

# Run migrations (if any)
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Reload web app (from Web tab)
```

## Backing Up Your Data

### Backup Database

```bash
# In PythonAnywhere bash console
mysqldump -u username -p -h username.mysql.pythonanywhere-services.com username$palmcash_db > backup.sql
```

### Backup Files

```bash
# Zip your project
cd ~
zip -r palmcash_backup.zip palmcash/

# Download from Files tab
```

## Performance Tips

1. **Enable caching**: Add Redis caching in settings
2. **Optimize queries**: Use `select_related()` and `prefetch_related()`
3. **Compress static files**: Use WhiteNoise middleware
4. **Monitor CPU usage**: Check Web tab for CPU time
5. **Use CDN**: For static files (optional)

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] `SECRET_KEY` is unique and strong
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] HTTPS enabled (Force HTTPS)
- [ ] Database password is strong
- [ ] Email credentials are app-specific passwords
- [ ] `.env` file is NOT in version control
- [ ] Regular backups scheduled

## Monitoring

### Check Error Logs

1. Go to **Web** tab
2. Click **Error log** link
3. Review recent errors

### Check Access Logs

1. Go to **Web** tab
2. Click **Access log** link
3. Review recent requests

### Monitor CPU Usage

1. Go to **Web** tab
2. Check CPU time usage
3. Optimize if exceeding limits

## Custom Domain (Optional)

To use your own domain:

1. Go to **Web** tab
2. Scroll to **Domains** section
3. Add your domain
4. Update DNS records (instructions provided)
5. Wait for DNS propagation (24-48 hours)

## Scaling Up

If you need more resources:

1. Upgrade PythonAnywhere plan
2. Increase CPU/memory allocation
3. Add more web workers
4. Use paid database plan

## Support

- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **Django Documentation**: https://docs.djangoproject.com/
- **Palm Cash Issues**: Check GitHub issues

## Quick Reference Commands

```bash
# Activate environment
workon palmcash-env

# Deactivate environment
deactivate

# Pull latest code
cd ~/palmcash && git pull origin main

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Access Django shell
python manage.py shell

# View error log
# Go to Web tab → Error log

# Reload web app
# Go to Web tab → Click Reload button
```

## Deployment Checklist

- [ ] PythonAnywhere account created
- [ ] Code pushed to GitHub
- [ ] Repository cloned on PythonAnywhere
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] MySQL database created
- [ ] `.env` file configured
- [ ] Migrations run
- [ ] Superuser created
- [ ] Static files collected
- [ ] WSGI file configured
- [ ] Virtual environment path set
- [ ] Static files mapping configured
- [ ] Web app reloaded
- [ ] Site accessible at https://username.pythonanywhere.com
- [ ] Admin panel working
- [ ] Email configured (optional)
- [ ] SSL/HTTPS enabled
- [ ] Backups scheduled

## Next Steps

1. Monitor your application for errors
2. Set up automated backups
3. Configure email notifications
4. Add custom domain (optional)
5. Monitor performance and optimize
6. Plan for scaling if needed

---

**Congratulations!** Your Palm Cash application is now live on PythonAnywhere! 🚀

For questions or issues, check the troubleshooting section or contact PythonAnywhere support.
