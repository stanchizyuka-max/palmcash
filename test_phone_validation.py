#!/usr/bin/env python
"""
Test phone number validation to see if 055 and 057 are accepted
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from accounts.forms import validate_zambian_phone
from django.core.exceptions import ValidationError

print("\n" + "="*70)
print("TEST PHONE NUMBER VALIDATION")
print("="*70)

test_numbers = [
    '0555123456',  # Zamtel (new)
    '0575123456',  # Airtel (new)
    '0955123456',  # Zamtel (old)
    '0965123456',  # MTN (old)
    '0975123456',  # Airtel (old)
    '0765123456',  # Zamtel (old)
    '0775123456',  # MTN (old)
    '+260555123456',  # With country code
    '260575123456',   # With country code no +
    '0512345678',  # Invalid (not a valid prefix)
    '0999999999',  # Invalid (099 not valid)
]

print(f"\n📱 Testing phone numbers:")
print(f"{'='*70}")

for number in test_numbers:
    try:
        result = validate_zambian_phone(number)
        print(f"✅ {number:20} - ACCEPTED (cleaned: {result})")
    except ValidationError as e:
        print(f"❌ {number:20} - REJECTED ({e.message})")

print(f"\n{'='*70}")
print(f"EXPECTED RESULTS:")
print(f"{'='*70}")
print(f"✅ Should accept: 055, 057, 095, 096, 097, 076, 077")
print(f"❌ Should reject: 051, 099, and other invalid prefixes")

print(f"\n💡 If 055 and 057 are still rejected:")
print(f"   1. The Django server needs to be restarted")
print(f"   2. Run: sudo systemctl restart gunicorn")
print(f"   3. Or: sudo systemctl restart uwsgi")
print(f"   4. Or restart your development server")

print(f"\n{'='*70}\n")
