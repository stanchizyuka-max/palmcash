# PythonAnywhere Quick Reference

Quick reference guide for common PythonAnywhere commands and tasks.

## Accessing PythonAnywhere

1. Go to https://www.pythonanywhere.com/
2. Log in with your credentials
3. Click **Bash console** to open terminal

## Virtual Environment Commands

```bash
# List all virtual environments
lsvirtualenv

# Create new virtual environment
mkvirtualenv --python=/usr/bin/python3.11 palmcash-env

# Activate virtual environment
workon palmcash-env

# Deactivate virtual environment
deactivate

# Delete virtual environment
rmvirtualenv palmcash-env
```

## Git Commands

```bash
# Clone repository
git clone https://github.com/yourusername/palmcash.git

# Navigate to project
cd palmcash

# Check status
git status

# Pull latest changes
git pull origin main

# Add changes
git add .

# Commit changes
git commit -m "Your message"

# Push changes
git push origin main
```

## Django Commands

```bash
# Activate environment first
workon palmcash-env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Create migrations
python manage.py makemigrations

# Run tests
python manage.py test

# Access Django shell
python manage.py shell

# Check for issues
python manage.py check
```

## Database Commands

```bash
# Connect to MySQL
mysql -u username -p -h username.mysql.pythonanywhere-services.com

# In MySQL prompt:
SHOW DATABASES;
USE username$palmcash_db;
SHOW TABLES;
SELECT COUNT(*) FROM accounts_user;
EXIT;

# Backup database
mysqldump -u username -p -h username.mysql.pythonanywhere-services.com username$palmcash_db > backup.sql

# Restore database
mysql -u username -p -h username.mysql.pythonanywhere-services.com username$palmcash_db < backup.sql
```

## File Management

```bash
# List files
ls -la

# Create directory
mkdir directory_name

# Remove file
rm filename

# Remove directory
rm -r directory_name

# Copy file
cp source destination

# Move file
mv source destination

# Edit file
nano filename
# (Ctrl+X to exit, Y to save)

# View file
cat filename

# Search in file
grep "search_term" filename
```

## Environment Variables

```bash
# View .env file
cat .env

# Edit .env file
nano .env
# (Ctrl+X to exit, Y to save)

# Load environment variables
export $(cat .env | xargs)

# Check if variable is set
echo $DB_NAME
```

## Pip Commands

```bash
# List installed packages
pip list

# Install package
pip install package_name

# Install from requirements
pip install -r requirements.txt

# Upgrade package
pip install --upgrade package_name

# Uninstall package
pip uninstall package_name

# Check for outdated packages
pip list --outdated
```

## Web App Management

### From Web Tab

1. **Reload Web App**
   - Go to Web tab
   - Click "Reload" button
   - Wait 10-20 seconds

2. **View Error Log**
   - Go to Web tab
   - Click "Error log" link
   - Review recent errors

3. **View Access Log**
   - Go to Web tab
   - Click "Access log" link
   - Review recent requests

4. **Configure WSGI**
   - Go to Web tab
   - Click WSGI configuration file link
   - Edit and save

5. **Configure Static Files**
   - Go to Web tab
   - Scroll to "Static files" section
   - Add/edit mappings

## Common Tasks

### Update Application

```bash
# Activate environment
workon palmcash-env

# Navigate to project
cd ~/palmcash

# Pull latest code
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Reload web app (from Web tab)
```

### Create Backup

```bash
# Backup database
mysqldump -u username -p -h username.mysql.pythonanywhere-services.com username$palmcash_db > backup_$(date +%Y%m%d).sql

# Backup files
cd ~
zip -r palmcash_backup_$(date +%Y%m%d).zip palmcash/
```

### Restore Backup

```bash
# Restore database
mysql -u username -p -h username.mysql.pythonanywhere-services.com username$palmcash_db < backup_20240101.sql

# Restore files
unzip palmcash_backup_20240101.zip
```

### Check Application Status

```bash
# Activate environment
workon palmcash-env

# Navigate to project
cd ~/palmcash

# Check Django
python manage.py check

# Test database connection
python manage.py dbshell
# (Type EXIT to exit)

# Run tests
python manage.py test
```

### View Logs

```bash
# View error log (from Web tab)
# Go to Web tab → Error log

# View access log (from Web tab)
# Go to Web tab → Access log

# View application output
# Check error log for detailed errors
```

## Troubleshooting Commands

```bash
# Check Python version
python --version

# Check virtual environment
which python

# Check installed packages
pip list | grep django

# Check database connection
python manage.py dbshell

# Check static files
ls -la staticfiles/

# Check media files
ls -la media/

# Check .env file
cat .env

# Check WSGI file
cat /var/www/username_pythonanywhere_com_wsgi.py
```

## Performance Monitoring

```bash
# Check disk usage
du -sh ~

# Check project size
du -sh ~/palmcash

# Check database size
mysql -u username -p -h username.mysql.pythonanywhere-services.com -e "SELECT table_schema, ROUND(SUM(data_length+index_length)/1024/1024,2) FROM information_schema.tables GROUP BY table_schema;"

# Check CPU usage
# Go to Web tab → Check CPU time
```

## Security Commands

```bash
# Change file permissions
chmod 600 .env

# Check file permissions
ls -la .env

# Generate new SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Check for security issues
python manage.py check --deploy
```

## Useful Shortcuts

```bash
# Go to project directory
cd ~/palmcash

# Activate environment and go to project
workon palmcash-env && cd ~/palmcash

# Quick status check
python manage.py check && echo "✓ All good!"

# Reload and check
touch /var/www/username_pythonanywhere_com_wsgi.py && echo "✓ Reloaded!"
```

## Important Paths

```
/home/username/                          # Home directory
/home/username/palmcash/                 # Project directory
/home/username/.virtualenvs/palmcash-env # Virtual environment
/home/username/palmcash/staticfiles/     # Static files
/home/username/palmcash/media/           # Media files
/var/www/username_pythonanywhere_com_wsgi.py  # WSGI file
```

## Important URLs

```
https://www.pythonanywhere.com/user/username/  # Dashboard
https://username.pythonanywhere.com/            # Your site
https://username.pythonanywhere.com/admin/      # Admin panel
https://username.pythonanywhere.com/dashboard/  # Dashboard
```

## Getting Help

- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **Django Docs**: https://docs.djangoproject.com/
- **Error Log**: Check Web tab → Error log
- **Support**: Contact PythonAnywhere support

## Quick Checklist

- [ ] Virtual environment activated
- [ ] Project directory correct
- [ ] Dependencies installed
- [ ] Database connected
- [ ] Migrations run
- [ ] Static files collected
- [ ] Web app reloaded
- [ ] Site accessible
- [ ] Admin panel working

---

**Tip**: Bookmark this page for quick reference while working on PythonAnywhere!
