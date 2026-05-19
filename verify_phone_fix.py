#!/usr/bin/env python
"""
Verify that phone validation is working correctly after the fix.
Run this on the server after restarting services.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from accounts.forms import validate_zambian_phone
from django.core.exceptions import ValidationError

def test_phone_validation():
    """Test phone validation with various numbers"""
    
    print("=" * 70)
    print("PHONE VALIDATION VERIFICATION")
    print("=" * 70)
    print()
    
    # Test cases: (number, should_pass, description)
    test_cases = [
        ('0555123456', True, 'Zamtel 055 prefix'),
        ('0575123456', True, 'Airtel 057 prefix'),
        ('0955123456', True, 'MTN 095 prefix'),
        ('0965123456', True, 'Airtel 096 prefix'),
        ('0975123456', True, 'Zamtel 097 prefix'),
        ('0765123456', True, 'MTN 076 prefix'),
        ('0775123456', True, 'Zamtel 077 prefix'),
        ('+260555123456', True, 'Zamtel 055 with country code'),
        ('260575123456', True, 'Airtel 057 with country code (no +)'),
        ('0512345678', False, 'Invalid 051 prefix'),
        ('0999999999', False, 'Invalid 099 prefix'),
        ('0501234567', False, 'Invalid 050 prefix'),
        ('12345', False, 'Too short'),
        ('09551234567890', False, 'Too long'),
    ]
    
    passed = 0
    failed = 0
    
    for number, should_pass, description in test_cases:
        try:
            result = validate_zambian_phone(number)
            if should_pass:
                print(f"✅ PASS: {number:20} - {description}")
                passed += 1
            else:
                print(f"❌ FAIL: {number:20} - {description} (should have been rejected)")
                failed += 1
        except ValidationError as e:
            if not should_pass:
                print(f"✅ PASS: {number:20} - {description} (correctly rejected)")
                passed += 1
            else:
                print(f"❌ FAIL: {number:20} - {description}")
                print(f"         Error: {e.message}")
                failed += 1
    
    print()
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print()
        print("🎉 SUCCESS! All phone validation tests passed!")
        print()
        print("✅ The fix is working correctly.")
        print("✅ Numbers starting with 055 and 057 are now accepted.")
        print()
        return True
    else:
        print()
        print("⚠️  SOME TESTS FAILED!")
        print()
        print("Possible issues:")
        print("1. Server not restarted properly")
        print("2. Python cache not cleared")
        print("3. Wrong version of forms.py on server")
        print()
        print("Try:")
        print("  sudo systemctl restart gunicorn")
        print("  find . -name '*.pyc' -delete")
        print()
        return False

if __name__ == '__main__':
    success = test_phone_validation()
    sys.exit(0 if success else 1)
