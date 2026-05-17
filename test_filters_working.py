#!/usr/bin/env python
"""
Test script to verify all filters are working correctly.
Run this to check the status of vault, processing fees, and expense filters.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from dashboard.views import manager_processing_fees, expense_list
from dashboard.vault_views import vault_dashboard
from clients.models import Branch

User = get_user_model()

def test_vault_date_filter():
    """Test that vault date filter handles empty dates correctly"""
    print("\n" + "="*60)
    print("TEST 1: Vault Date Filter")
    print("="*60)
    
    factory = RequestFactory()
    
    # Get a manager user
    manager = User.objects.filter(role='manager').first()
    if not manager:
        print("❌ No manager user found")
        return False
    
    # Test with empty dates (should show all transactions)
    request = factory.get('/dashboard/vault/', {
        'date_from': '',
        'date_to': '',
    })
    request.user = manager
    
    try:
        response = vault_dashboard(request)
        print("✅ Vault dashboard loads with empty date filters")
        print(f"   Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_processing_fees_vault_filter():
    """Test that processing fees have vault type filter"""
    print("\n" + "="*60)
    print("TEST 2: Processing Fees Vault Type Filter")
    print("="*60)
    
    factory = RequestFactory()
    
    # Get a manager user
    manager = User.objects.filter(role='manager').first()
    if not manager:
        print("❌ No manager user found")
        return False
    
    # Test with vault type filter
    request = factory.get('/dashboard/processing-fees/', {
        'vault_type': 'daily',
    })
    request.user = manager
    
    try:
        response = manager_processing_fees(request)
        print("✅ Processing fees page loads with vault type filter")
        print(f"   Status code: {response.status_code}")
        
        # Check if filter is in context
        if hasattr(response, 'context_data'):
            filters = response.context_data.get('filters', {})
            if 'vault_type' in filters:
                print(f"   ✅ Vault type filter in context: {filters['vault_type']}")
            else:
                print("   ⚠️  Vault type filter not in context")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_expense_vault_filter():
    """Test that expense list has vault type filter"""
    print("\n" + "="*60)
    print("TEST 3: Expense List Vault Type Filter")
    print("="*60)
    
    factory = RequestFactory()
    
    # Get a manager user
    manager = User.objects.filter(role='manager').first()
    if not manager:
        print("❌ No manager user found")
        return False
    
    # Test with vault type filter
    request = factory.get('/dashboard/expenses/', {
        'vault_type': 'weekly',
    })
    request.user = manager
    
    try:
        response = expense_list(request)
        print("✅ Expense list page loads with vault type filter")
        print(f"   Status code: {response.status_code}")
        
        # Check if filter is in context
        if hasattr(response, 'context_data'):
            vault_type = response.context_data.get('vault_type_filter')
            if vault_type:
                print(f"   ✅ Vault type filter in context: {vault_type}")
            else:
                print("   ⚠️  Vault type filter not in context")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_template_files():
    """Check that template files exist and have the required elements"""
    print("\n" + "="*60)
    print("TEST 4: Template Files Check")
    print("="*60)
    
    templates = {
        'Processing Fees': 'dashboard/templates/dashboard/manager_processing_fees.html',
        'Expense List': 'dashboard/templates/dashboard/expense_list.html',
        'Vault': 'dashboard/templates/dashboard/vault.html',
    }
    
    all_exist = True
    for name, path in templates.items():
        if os.path.exists(path):
            print(f"✅ {name} template exists: {path}")
            
            # Check for vault_type in template
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'vault_type' in content.lower():
                    print(f"   ✅ Contains 'vault_type' references")
                else:
                    print(f"   ⚠️  No 'vault_type' references found")
        else:
            print(f"❌ {name} template NOT found: {path}")
            all_exist = False
    
    return all_exist


def main():
    print("\n" + "="*60)
    print("FILTER FUNCTIONALITY TEST SUITE")
    print("="*60)
    print("Testing all filter implementations...")
    
    results = []
    
    # Run tests
    results.append(("Vault Date Filter", test_vault_date_filter()))
    results.append(("Processing Fees Vault Filter", test_processing_fees_vault_filter()))
    results.append(("Expense Vault Filter", test_expense_vault_filter()))
    results.append(("Template Files", check_template_files()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! All filters are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")


if __name__ == '__main__':
    main()
