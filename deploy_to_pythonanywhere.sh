#!/bin/bash

# PythonAnywhere Deployment Script for Palm Cash Dashboard Fixes
# Date: January 7, 2026
# Changes: Manager dashboard fixes for security deposits and disbursed loans

echo "=========================================="
echo "DEPLOYING TO PYTHONANYWHERE"
echo "=========================================="

# NOTE: Replace 'username' with your actual PythonAnywhere username
# You need to run these commands on PythonAnywhere via SSH

echo ""
echo "STEP 1: Navigate to project directory"
echo "cd /home/username/palmcash"

echo ""
echo "STEP 2: Pull latest changes from GitHub"
echo "git pull origin main"

echo ""
echo "STEP 3: Activate virtual environment"
echo "source /home/username/.virtualenvs/palmcash/bin/activate"

echo ""
echo "STEP 4: Install any new dependencies"
echo "pip install -r requirements.txt"

echo ""
echo "STEP 5: Run migrations (if any)"
echo "python palmcash/manage.py migrate"

echo ""
echo "STEP 6: Collect static files"
echo "python palmcash/manage.py collectstatic --noinput"

echo ""
echo "STEP 7: Reload the web application"
echo "touch /var/www/username_pythonanywhere_com_wsgi.py"

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "VERIFICATION STEPS:"
echo "1. Visit your PythonAnywhere site"
echo "2. Check manager dashboard for:"
echo "   - Pending security deposits count"
echo "   - Correct disbursed loans amount"
echo "3. Verify no errors in dashboard"
echo ""
echo "If issues occur, check error logs in PythonAnywhere web console"
