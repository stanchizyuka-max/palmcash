"""
Script to set up officer assignments for existing loan officers
Run this after implementing the group assignment system

Usage: python setup_officer_assignments.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from accounts.models import User
from clients.models import OfficerAssignment


def setup_officer_assignments():
    """Create OfficerAssignment records for all loan officers"""
    
    loan_officers = User.objects.filter(role='loan_officer')
    
    if not loan_officers.exists():
        print("⚠️  No loan officers found in the system.")
        print("   Create loan officers first before running this script.")
        return
    
    print(f"Found {loan_officers.count()} loan officer(s)")
    print("="*60)
    
    created_count = 0
    existing_count = 0
    
    for officer in loan_officers:
        assignment, created = OfficerAssignment.objects.get_or_create(
            officer=officer,
            defaults={
                'max_groups': 5,
                'max_clients': 50,
                'is_accepting_assignments': True
            }
        )
        
        if created:
            created_count += 1
            print(f"✓ Created assignment for: {officer.full_name} ({officer.email})")
            print(f"  - Max Groups: {assignment.max_groups}")
            print(f"  - Max Clients: {assignment.max_clients}")
            print(f"  - Accepting Assignments: {assignment.is_accepting_assignments}")
        else:
            existing_count += 1
            print(f"↻ Assignment already exists for: {officer.full_name}")
            print(f"  - Current Groups: {assignment.current_group_count}/{assignment.max_groups}")
            print(f"  - Current Clients: {assignment.current_client_count}/{assignment.max_clients}")
        
        print()
    
    print("="*60)
    print(f"Summary:")
    print(f"  Created: {created_count} assignments")
    print(f"  Existing: {existing_count} assignments")
    print(f"  Total: {created_count + existing_count} assignments")
    print("="*60)
    print("\n✓ Officer assignments setup complete!")
    print("\nNext steps:")
    print("1. Create borrower groups: /clients/groups/create/")
    print("2. Assign officers to groups")
    print("3. Add borrowers to groups")
    print("4. Monitor workload: /clients/officers/workload/")


if __name__ == '__main__':
    print("Setting up officer assignments...")
    print("="*60)
    setup_officer_assignments()
