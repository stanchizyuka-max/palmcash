#!/bin/bash

# Processing Fee Deployment Script
# Run this on the server to deploy processing fee feature

echo "=========================================="
echo "PROCESSING FEE DEPLOYMENT"
echo "=========================================="
echo ""

# Step 1: Pull latest code
echo "Step 1: Pulling latest code from GitHub..."
git pull origin main
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to pull code"
    exit 1
fi
echo "✓ Code pulled successfully"
echo ""

# Step 2: Clear Python cache
echo "Step 2: Clearing Python cache..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo "✓ Cache cleared"
echo ""

# Step 3: Run migrations
echo "Step 3: Running database migrations..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "❌ Error: Migration failed"
    exit 1
fi
echo "✓ Migrations completed"
echo ""

# Step 4: Restart server
echo "Step 4: Restarting Gunicorn server..."
sudo systemctl restart gunicorn
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to restart server"
    exit 1
fi
echo "✓ Server restarted"
echo ""

# Step 5: Check server status
echo "Step 5: Checking server status..."
sleep 2
sudo systemctl status gunicorn --no-pager | head -n 10
echo ""

echo "=========================================="
echo "✓ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test the vault page in your browser"
echo "2. Check if 'Processing Fee' appears in the filter dropdown"
echo "3. Run: python identify_processing_fees.py"
echo ""
