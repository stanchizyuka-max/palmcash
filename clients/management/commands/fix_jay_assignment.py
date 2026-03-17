from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clients.models import OfficerAssignment, Branch

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix Jay OfficerAssignment for branch visibility'

    def handle(self, *args, **options):
        self.stdout.write("Fixing Jay's OfficerAssignment...")

        jay = User.objects.filter(username='jay').first()
        if not jay:
            self.stdout.write(self.style.ERROR('Jay user not found'))
            return

        self.stdout.write(f"Found: {jay.get_full_name()} | role: {jay.role}")

        assignment = OfficerAssignment.objects.filter(officer=jay).first()

        if assignment:
            self.stdout.write(f"OfficerAssignment exists | branch: '{assignment.branch}'")
        else:
            self.stdout.write("No OfficerAssignment — creating one...")

            kamwala = Branch.objects.filter(name__icontains='kamwala').first()
            if not kamwala:
                self.stdout.write("Kamwala branch not found. Available branches:")
                for b in Branch.objects.all():
                    self.stdout.write(f"  - {b.name}")
                kamwala = Branch.objects.create(name='Kamwala', code='KM', location='Kamwala, Lusaka')
                self.stdout.write(self.style.SUCCESS(f"Created branch: {kamwala.name}"))

            assignment = OfficerAssignment.objects.create(
                officer=jay,
                branch=kamwala.name,
                max_groups=15,
                max_clients=50,
            )
            self.stdout.write(self.style.SUCCESS(f"Created OfficerAssignment | branch: '{assignment.branch}'"))

        if not assignment.branch:
            self.stdout.write(self.style.WARNING("Branch is empty on assignment"))

        from loans.models import LoanApplication
        apps = LoanApplication.objects.filter(loan_officer=jay)
        self.stdout.write(f"\nJay's applications: {apps.count()}")
        for app in apps:
            self.stdout.write(f"  {app.application_number}: {app.borrower.get_full_name()} — {app.status}")

        if assignment.branch:
            visible = LoanApplication.objects.filter(
                loan_officer__officer_assignment__branch=assignment.branch
            ).distinct()
            self.stdout.write(f"\nManager would see: {visible.count()} applications")
            for app in visible:
                self.stdout.write(f"  {app.application_number}: {app.borrower.get_full_name()} by {app.loan_officer.get_full_name()}")

        self.stdout.write(self.style.SUCCESS('\nDone.'))
