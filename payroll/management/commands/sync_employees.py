from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from payroll.models import Employee


class Command(BaseCommand):
    help = 'Sync all staff users (admins, managers, loan officers) as employees'
    
    def handle(self, *args, **options):
        # Get all staff users (not borrowers)
        staff_users = User.objects.filter(
            role__in=['admin', 'manager', 'loan_officer'],
            is_active=True
        ).order_by('date_joined')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for user in staff_users:
            # Check if employee record already exists
            employee, created = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': f'EMP{user.id:04d}',
                    'position': user.get_role_display(),
                    'hire_date': user.date_joined.date() if user.date_joined else timezone.now().date(),
                    'is_active': user.is_active,
                }
            )
            
            if created:
                # Try to get branch from officer assignment or managed branch
                branch_name = self.get_user_branch(user)
                if branch_name:
                    employee.branch = branch_name
                    employee.save()
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created employee: {employee.employee_id} - {user.get_full_name()}')
                )
            else:
                # Update existing employee
                updated = False
                
                # Update branch if not set
                if not employee.branch:
                    branch_name = self.get_user_branch(user)
                    if branch_name:
                        employee.branch = branch_name
                        updated = True
                
                # Update position if changed
                if employee.position != user.get_role_display():
                    employee.position = user.get_role_display()
                    updated = True
                
                # Update active status
                if employee.is_active != user.is_active:
                    employee.is_active = user.is_active
                    updated = True
                
                if updated:
                    employee.save()
                    updated_count += 1
                    self.stdout.write(f'  Updated: {employee.employee_id} - {user.get_full_name()}')
                else:
                    skipped_count += 1
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Sync completed!'))
        self.stdout.write(f'  Created: {created_count}')
        self.stdout.write(f'  Updated: {updated_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        self.stdout.write(f'  Total staff: {staff_users.count()}')
    
    def get_user_branch(self, user):
        """Get branch name for user"""
        try:
            # For managers - check managed_branch
            if user.role == 'manager' and hasattr(user, 'managed_branch'):
                return user.managed_branch.name
            
            # For loan officers - check officer_assignment
            if user.role == 'loan_officer':
                from clients.models import OfficerAssignment
                assignment = OfficerAssignment.objects.filter(officer=user).first()
                if assignment:
                    return assignment.branch
            
            return None
        except Exception:
            return None
