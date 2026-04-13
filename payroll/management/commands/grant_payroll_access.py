from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.sessions.models import Session
from django.utils import timezone
from accounts.models import User


class Command(BaseCommand):
    help = 'Grant or revoke payroll access to a specific user'
    
    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user')
        parser.add_argument(
            '--revoke',
            action='store_true',
            help='Revoke payroll access instead of granting'
        )
    
    def clear_user_sessions(self, user):
        """Clear all active sessions for a user"""
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        cleared = 0
        for session in active_sessions:
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(user.id):
                session.delete()
                cleared += 1
        return cleared
    
    def handle(self, *args, **options):
        username = options['username']
        revoke = options.get('revoke', False)
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return
        
        try:
            # Get payroll permissions
            view_perm = Permission.objects.get(codename='can_view_payroll')
            manage_perm = Permission.objects.get(codename='can_manage_payroll')
            report_perm = Permission.objects.get(codename='can_generate_payroll_reports')
            
            if revoke:
                user.user_permissions.remove(view_perm, manage_perm, report_perm)
                
                # Clear user sessions to force re-login
                cleared = self.clear_user_sessions(user)
                
                self.stdout.write(
                    self.style.SUCCESS(f'✗ Revoked payroll access from {user.get_full_name()}')
                )
                if cleared > 0:
                    self.stdout.write(f'  - Cleared {cleared} active session(s) - user will be logged out')
            else:
                user.user_permissions.add(view_perm, manage_perm, report_perm)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Granted payroll access to {user.get_full_name()}')
                )
                self.stdout.write(f'  - can_view_payroll: ✓')
                self.stdout.write(f'  - can_manage_payroll: ✓')
                self.stdout.write(f'  - can_generate_payroll_reports: ✓')
                self.stdout.write(f'  - User must logout and login for changes to take effect')
        except Permission.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Payroll permissions not found. Run migrations first: python manage.py migrate payroll')
            )
