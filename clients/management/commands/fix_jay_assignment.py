from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clients.models import OfficerAssignment, Branch

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix Jay OfficerAssignment for branch visibility'
    
    def handle(self, *args, **options):
        self.stdout.write("🔧 Fixing Jay's OfficerAssignment...")
        
        # Find Jay user
        jay = User.objects.filter(username='jay').first()
        if not jay:
            self.stdout.write(self.style.ERROR('❌ Jay user not found'))
            return
        
        self.stdout.write(f"✅ Found Jay: {jay.get_full_name()} (username: {jay.username})")
        self.stdout.write(f"   Role: {jay.role}")
        
        # Check if Jay has OfficerAssignment
        try:
            assignment = jay.officer_assignment
            self.stdout.write(f"✅ Jay has OfficerAssignment:")
            self.stdout.write(f"   Branch: '{assignment.branch}'")
            self.stdout.write(f"   Max Groups: {assignment.max_groups}")
            self.stdout.write(f"   Max Clients: {assignment.max_clients}")
            
            if not assignment.branch:
                self.stdout.write(self.style.WARNING('⚠️  Branch is empty, need to set it'))
                
        except OfficerAssignment.DoesNotExist:
            self.stdout.write(self.style.WARNING('❌ Jay has NO OfficerAssignment - creating one...'))
            
            # Find Kamwala branch
            kamwala_branch = Branch.objects.filter(name__icontains='kamwala').first()
            if not kamwala_branch:
                self.stdout.write(self.style.ERROR('❌ Kamwala branch not found, checking all branches...'))
                all_branches = Branch.objects.all()
                for branch in all_branches:
                    self.stdout.write(f"   - {branch.name} (Manager: {branch.manager})")
                
                # Create Kamwala branch if it doesn't exist
                kamwala_branch = Branch.objects.create(
                    name='Kamwala',
                    code='KM',
                    location='Kamwala, Lusaka'
                )
                self.stdout.write(self.style.SUCCESS(f"✅ Created Kamwala branch: {kamwala_branch.name}"))
            
            # Create OfficerAssignment for Jay
            assignment = OfficerAssignment.objects.create(
                officer=jay,
                branch=kamwala_branch.name,
                max_groups=15,
                max_clients=50
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Created OfficerAssignment for Jay:"))
            self.stdout.write(f"   Branch: '{assignment.branch}'")
            self.stdout.write(f"   Max Groups: {assignment.max_groups}")
            self.stdout.write(f"   Max Clients: {assignment.max_clients}")
        
        # Check Jay's loan applications
        from loans.models import LoanApplication
        jay_apps = LoanApplication.objects.filter(loan_officer=jay)
        self.stdout.write(f"\n📋 Jay's Loan Applications: {jay_apps.count()}")
        for app in jay_apps:
            self.stdout.write(f"   - {app.application_number}: {app.borrower.get_full_name()} - {app.status}")
        
        # Check what manager would see
        if assignment and assignment.branch:
            manager_branch = assignment.branch
            manager_apps = LoanApplication.objects.filter(
                loan_officer__officer_assignment__branch=manager_branch
            ).distinct()
            self.stdout.write(f"\n👨‍💼 Manager would see: {manager_apps.count()} applications")
            for app in manager_apps:
                self.stdout.write(f"   - {app.application_number}: {app.borrower.get_full_name()} by {app.loan_officer.get_full_name()}")
        
        self.stdout.write(self.style.SUCCESS('\n✅ Jay assignment fix completed!'))
