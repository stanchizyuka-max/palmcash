#!/usr/bin/env python
"""
Simple fix - temporarily show all collections to all users
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from payments.models import PaymentCollection


def simple_fix():
    """Temporarily modify collection details view to show all collections"""
    
    print("Creating simple fix for collection details...")
    
    # Read the current views.py file
    views_file = os.path.join(os.path.dirname(__file__), 'dashboard', 'views.py')
    
    with open(views_file, 'r') as f:
        content = f.read()
    
    # Find the collection_details function and replace role-based filtering
    old_function = '''def collection_details(request):
    """Collection Details View - Shows detailed collection information"""
    user = request.user
    
    if user.role == 'manager':
        # Manager sees collections for their branch
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
        
        collections = PaymentCollection.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name
        ).order_by('-collection_date')
    elif user.role == 'loan_officer':
        # Loan officer sees their collections
        collections = PaymentCollection.objects.filter(
            loan__loan_officer=user
        ).order_by('-collection_date')
    elif user.role == 'admin':
        # Admin sees all collections
        collections = PaymentCollection.objects.all().order_by('-collection_date')
    else:
        return render(request, 'dashboard/access_denied.html')'''
    
    new_function = '''def collection_details(request):
    """Collection Details View - Shows detailed collection information"""
    user = request.user
    
    # TEMPORARY FIX: Show all collections to all logged-in users
    if user.is_authenticated:
        collections = PaymentCollection.objects.all().order_by('-collection_date')
    else:
        return render(request, 'dashboard/access_denied.html')'''
    
    # Replace the function
    if old_function in content:
        content = content.replace(old_function, new_function)
        
        with open(views_file, 'w') as f:
            f.write(content)
        
        print("✅ Successfully updated collection_details view!")
        print("All users will now see all collections temporarily.")
    else:
        print("❌ Could not find the collection_details function to replace")


if __name__ == "__main__":
    simple_fix()
