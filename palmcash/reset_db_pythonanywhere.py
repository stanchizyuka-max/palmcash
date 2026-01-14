#!/usr/bin/env python
"""
Script to reset the database on PythonAnywhere
Run this from PythonAnywhere's web console or bash console
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

print("=" * 60)
print("DATABASE RESET SCRIPT (PythonAnywhere)")
print("=" * 60)

# Confirm before proceeding
confirm = input("\n⚠️  WARNING: This will DELETE ALL DATA in the database!\nAre you sure? (type 'yes' to confirm): ")
if confirm.lower() != 'yes':
    print("Reset cancelled.")
    sys.exit(0)

try:
    print("\n1. Flushing all data...")
    call_command('flush', '--no-input', verbosity=2)
    print("   ✓ All data flushed")
    
    print("\n2. Running migrations...")
    call_command('migrate', verbosity=2)
    print("   ✓ Migrations completed")
    
    print("\n" + "=" * 60)
    print("✓ DATABASE RESET COMPLETE!")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Create a superuser: python manage.py createsuperuser")
    print("2. Create staff users (loan officers, managers, admins)")
    print("3. Create borrowers and start testing")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
