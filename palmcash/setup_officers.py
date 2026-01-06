#!/usr/bin/env python
"""
Script to assign all loan officers to the main branch
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from accounts.models import User
from clients.models import OfficerAssignment, Branch

officers = User.objects.filter(role='loan_officer')
print(f'Total officers: {officers.count()}')

branch = Branch.objects.first()
if branch:
    print(f'Main branch: {branch.name}')
    
    # Assign all officers to the main branch
    for officer in officers:
        assignment, created = OfficerAssignment.objects.get_or_create(officer=officer)
        assignment.branch = branch.name
        assignment.save()
        status = 'created' if created else 'updated'
        print(f'  ✓ {officer.full_name}: {status} assignment to {branch.name}')
    
    print('\nAll officers assigned to main branch!')
else:
    print('No branches found')
