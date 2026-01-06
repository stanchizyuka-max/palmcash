#!/usr/bin/env python
"""
Script to assign all borrower groups to the main branch
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from clients.models import BorrowerGroup, Branch

groups = BorrowerGroup.objects.all()
print(f'Total groups: {groups.count()}')

branch = Branch.objects.first()
if branch:
    print(f'Main branch: {branch.name}')
    
    # Assign all groups to the main branch
    for group in groups:
        group.branch = branch.name
        group.save()
        print(f'  ✓ {group.name}: assigned to {branch.name}')
    
    print('\nAll groups assigned to main branch!')
else:
    print('No branches found')
