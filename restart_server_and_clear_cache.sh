#!/bin/bash

echo "======================================================================="
echo "RESTART SERVER AND CLEAR CACHE"
echo "======================================================================="

# Step 1: Clear Python bytecode cache
echo ""
echo "Step 1: Clearing Python bytecode cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✅ Cache cleared"

# Step 2: Restart Gunicorn (if using Gunicorn)
echo ""
echo "Step 2: Restarting Gunicorn..."
if sudo systemctl restart gunicorn 2>/dev/null; then
    echo "✅ Gunicorn restarted successfully"
    sudo systemctl status gunicorn --no-pager | head -10
else
    echo "⚠️  Gunicorn service not found or failed to restart"
fi

# Step 3: Restart uWSGI (if using uWSGI)
echo ""
echo "Step 3: Checking for uWSGI..."
if sudo systemctl restart uwsgi 2>/dev/null; then
    echo "✅ uWSGI restarted successfully"
    sudo systemctl status uwsgi --no-pager | head -10
else
    echo "⚠️  uWSGI service not found (this is OK if using Gunicorn)"
fi

# Step 4: Restart Nginx (optional but recommended)
echo ""
echo "Step 4: Restarting Nginx..."
if sudo systemctl restart nginx 2>/dev/null; then
    echo "✅ Nginx restarted successfully"
else
    echo "⚠️  Nginx service not found or failed to restart"
fi

echo ""
echo "======================================================================="
echo "RESTART COMPLETE"
echo "======================================================================="
echo ""
echo "📝 NEXT STEPS:"
echo "1. Clear your browser cache (Ctrl+Shift+Delete)"
echo "2. Try registering with a 055 or 057 number"
echo "3. If still not working, try in an incognito/private window"
echo ""
echo "======================================================================="
