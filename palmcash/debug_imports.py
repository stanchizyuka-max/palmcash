#!/usr/bin/env python
"""
Debug script to check for import errors
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

print("=== TESTING IMPORTS ===")

try:
    from loans.models import SecurityDeposit
    print("✅ SecurityDeposit import: SUCCESS")
except Exception as e:
    print(f"❌ SecurityDeposit import: {e}")

try:
    from dashboard.views import approved_security_deposits
    print("✅ approved_security_deposits import: SUCCESS")
except Exception as e:
    print(f"❌ approved_security_deposits import: {e}")

try:
    from django.db.models import Sum
    print("✅ Sum import: SUCCESS")
except Exception as e:
    print(f"❌ Sum import: {e}")

try:
    from django.core.paginator import Paginator
    print("✅ Paginator import: SUCCESS")
except Exception as e:
    print(f"❌ Paginator import: {e}")

print("\n=== TESTING SECURITY DEPOSIT MODEL ===")
try:
    from loans.models import SecurityDeposit
    count = SecurityDeposit.objects.count()
    print(f"✅ SecurityDeposit objects count: {count}")
except Exception as e:
    print(f"❌ SecurityDeposit query: {e}")

print("\n=== END DEBUG ===")
