#!/bin/bash
# Script to apply pending migrations on PythonAnywhere

echo "Applying Django migrations..."
python manage.py migrate

echo ""
echo "Checking migration status..."
python manage.py showmigrations loans

echo ""
echo "Done! Migrations have been applied."
