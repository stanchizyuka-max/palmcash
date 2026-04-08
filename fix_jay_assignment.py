#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.contrib.auth.models import User
from clients.models import OfficerAssignment, Branch

def fix_jay_assignment():
    """Check and fix Jay's OfficerAssignment"""
    
    # Find Jay user
    jay = User.objects.filter(username='jay').first()
    if not jay:
        print("❌ Jay user not found")
        return
    
    print(f"✅ Found Jay: {jay.get_full_name()} (username: {jay.username})")
    print(f"   Role: {jay.role}")
    
    # Check if Jay has OfficerAssignment
    try:
        assignment = jay.officer_assignment
        print(f"✅ Jay has OfficerAssignment:")
        print(f"   Branch: '{assignment.branch}'")
        print(f"   Max Groups: {assignment.max_groups}")
        print(f"   Max Clients: {assignment.max_clients}")
        
        if not assignment.branch:
            print("⚠️  Branch is empty, need to set it")
            
    except OfficerAssignment.DoesNotExist:
        print("❌ Jay has NO OfficerAssignment - creating one...")
        
        # Find Kamwala branch
        kamwala_branch = Branch.objects.filter(name__icontains='kamwala').first()
        if not kamwala_branch:
            print("❌ Kamwala branch not found, checking all branches...")
            all_branches = Branch.objects.all()
            for branch in all_branches:
                print(f"   - {branch.name} (Manager: {branch.manager})")
            
            # Create Kamwala branch if it doesn't exist
            kamwala_branch = Branch.objects.create(
                name='Kamwala',
                code='KM',
                location='Kamwala, Lusaka'
            )
            print(f"✅ Created Kamwala branch: {kamwala_branch.name}")
        
        # Create OfficerAssignment for Jay
        assignment = OfficerAssignment.objects.create(
            officer=jay,
            branch=kamwala_branch.name,
            max_groups=15,
            max_clients=50
        )
        print(f"✅ Created OfficerAssignment for Jay:")
        print(f"   Branch: '{assignment.branch}'")
        print(f"   Max Groups: {assignment.max_groups}")
        print(f"   Max Clients: {assignment.max_clients}")
    
    # Check Jay's loan applications
    from loans.models import LoanApplication
    jay_apps = LoanApplication.objects.filter(loan_officer=jay)
    print(f"\n📋 Jay's Loan Applications: {jay_apps.count()}")
    for app in jay_apps:
        print(f"   - {app.application_number}: {app.borrower.get_full_name()} - {app.status}")
    
    # Check what manager would see
    if assignment and assignment.branch:
        manager_branch = assignment.branch
        manager_apps = LoanApplication.objects.filter(
            loan_officer__officer_assignment__branch=manager_branch
        ).distinct()
        print(f"\n👨‍💼 Manager would see: {manager_apps.count()} applications")
        for app in manager_apps:
            print(f"   - {app.application_number}: {app.borrower.get_full_name()} by {app.loan_officer.get_full_name()}")
    
    print("\n✅ Jay assignment fix completed!")

if __name__ == '__main__':
    fix_jay_assignment()
