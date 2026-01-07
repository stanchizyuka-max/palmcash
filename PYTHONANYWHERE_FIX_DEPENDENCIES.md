# Fix Missing Dependencies on PythonAnywhere

The error indicates that `widget_tweaks` is not installed in the virtual environment. Follow these steps to fix it:

## Quick Fix: Install Missing Packages

### Using PythonAnywhere Bash Console

1. Go to PythonAnywhere dashboard
2. Click on "Consoles" tab
3. Click on "Bash" to open a terminal
4. Run these commands:

```bash
cd /home/stan13/palmcash/palmcash
source /home/stan13/.virtualenvs/palmcash-env/bin/activate
pip install -r requirements.txt
```

This will install all required packages including `django-widget-tweaks`.

### Using SSH (if enabled)

```bash
ssh stan13@ssh.pythonanywhere.com
cd /home/stan13/palmcash/palmcash
source /home/stan13/.virtualenvs/palmcash-env/bin/activate
pip install -r requirements.txt
```

## After Installing Dependencies

1. Go to the Web tab
2. Click "Reload" to restart the app
3. The error should be resolved

## Verify Installation

To verify all packages are installed correctly:

```bash
pip list | grep -i widget
pip list | grep -i django
```

You should see:
- `django-widget-tweaks` (version 1.4.12 or higher)
- `Django` (version 4.2.7)
- `django-crispy-forms`
- `crispy-bootstrap5`

## If Issues Persist

If you still get import errors after installing:

1. Check Python version compatibility:
```bash
python --version
```

2. Verify the virtual environment is activated:
```bash
which python
```

3. Try reinstalling with upgrade flag:
```bash
pip install --upgrade -r requirements.txt
```

4. Clear pip cache:
```bash
pip cache purge
pip install -r requirements.txt
```

## Automated Fix

The WSGI file now includes automatic migration running. After installing dependencies and reloading the web app, migrations should run automatically.
