from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from loans.models import SecurityTopUpRequest, Loan

User = get_user_model()

class Command(BaseCommand):
    help = 'Debug missing security top-up request for Shucco Zulu'

    def handle(self, *args, **options):
        self.stdout.write("=== DEBUGGING SHUCCO ZULU TOP-UP REQUEST ===\n")
        
        # 1. Find Shucco Zulu client (borrower)
        try:
            client = User.objects.get(
                first_name__icontains='shucco',
                last_name__icontains='zulu',
                role='borrower'
            )
            self.stdout.write(f"✓ Found client: {client.first_name} {client.last_name}")
            self.stdout.write(f"  - Client ID: {client.id}")
            self.stdout.write(f"  - Role: {client.role}")
            self.stdout.write(f"  - Status: {client.is_verified}")
        except User.DoesNotExist:
            self.stdout.write("✗ Client 'Shucco Zulu' not found")
            # Try partial matches
            clients = User.objects.filter(
                first_name__icontains='shucco',
                role='borrower'
            ) | User.objects.filter(
                last_name__icontains='zulu',
                role='borrower'
            )
            if clients.exists():
                self.stdout.write("Similar clients found:")
                for c in clients:
                    self.stdout.write(f"  - {c.first_name} {c.last_name} (ID: {c.id})")
            return
        except User.MultipleObjectsReturned:
            clients = User.objects.filter(
                first_name__icontains='shucco',
                last_name__icontains='zulu',
                role='borrower'
            )
            self.stdout.write(f"Multiple clients found ({clients.count()}):")
            for c in clients:
                self.stdout.write(f"  - {c.first_name} {c.last_name} (ID: {c.id})")
            client = clients.first()
            self.stdout.write(f"Using first match: {client.first_name} {client.last_name}")

        # 2. Find Precious loan officer
        try:
            officer = User.objects.get(
                first_name__icontains='precious',
                role='loan_officer'
            )
            self.stdout.write(f"✓ Found loan officer: {officer.first_name} {officer.last_name}")
            self.stdout.write(f"  - Officer ID: {officer.id}")
            self.stdout.write(f"  - Branch: {officer.branch}")
            self.stdout.write(f"  - Role: {officer.role}")
        except User.DoesNotExist:
            self.stdout.write("✗ Loan officer 'Precious' not found")
            officers = User.objects.filter(
                first_name__icontains='precious'
            )
            if officers.exists():
                self.stdout.write("Similar officers found:")
                for o in officers:
                    self.stdout.write(f"  - {o.first_name} {o.last_name} (Role: {o.role})")
            return
        except User.MultipleObjectsReturned:
            officers = User.objects.filter(
                first_name__icontains='precious',
                role='loan_officer'
            )
            self.stdout.write(f"Multiple officers found ({officers.count()}):")
            for o in officers:
                self.stdout.write(f"  - {o.first_name} {o.last_name} (ID: {o.id})")
            officer = officers.first()

        # 3. Check client's loans
        loans = Loan.objects.filter(borrower=client)
        self.stdout.write(f"\n✓ Client has {loans.count()} loan(s):")
        for loan in loans:
            self.stdout.write(f"  - Loan {loan.loan_id}: {loan.status}")
            self.stdout.write(f"    Officer: {loan.loan_officer}")
            self.stdout.write(f"    Branch: {getattr(loan, 'branch', 'No branch')}")

        # 4. Check all top-up requests for this client
        topup_requests = SecurityTopUpRequest.objects.filter(
            loan__borrower=client
        ).order_by('-requested_date')
        
        self.stdout.write(f"\n✓ Found {topup_requests.count()} top-up request(s) for client:")
        for req in topup_requests:
            self.stdout.write(f"  - Amount: K{req.requested_amount}")
            self.stdout.write(f"    Status: {req.status}")
            self.stdout.write(f"    Requested by: {req.requested_by}")
            self.stdout.write(f"    Date: {req.requested_date}")
            self.stdout.write(f"    Loan: {req.loan.loan_id}")
            self.stdout.write(f"    Reason: {req.reason}")

        # 5. Check for K200 requests specifically
        k200_requests = SecurityTopUpRequest.objects.filter(
            loan__borrower=client,
            requested_amount=200
        )
        self.stdout.write(f"\n✓ K200 top-up requests: {k200_requests.count()}")
        for req in k200_requests:
            self.stdout.write(f"  - Status: {req.status}")
            self.stdout.write(f"    Requested by: {req.requested_by}")
            self.stdout.write(f"    Date: {req.requested_date}")

        # 6. Check pending requests by Precious
        precious_requests = SecurityTopUpRequest.objects.filter(
            requested_by=officer,
            status='pending'
        )
        self.stdout.write(f"\n✓ Pending requests by {officer.first_name}: {precious_requests.count()}")
        for req in precious_requests:
            self.stdout.write(f"  - Client: {req.loan.borrower}")
            self.stdout.write(f"    Amount: K{req.requested_amount}")
            self.stdout.write(f"    Date: {req.requested_date}")

        # 7. Check branch managers who should see the request
        managers = User.objects.filter(
            role='manager'
        )
        self.stdout.write(f"\n✓ All managers: {managers.count()}")
        for mgr in managers:
            self.stdout.write(f"  - {mgr.first_name} {mgr.last_name}")

        # 8. Check what pending requests managers can see
        if managers.exists():
            manager = managers.first()
            # For managers, they can see all pending requests (no branch filtering in current logic)
            visible_requests = SecurityTopUpRequest.objects.filter(
                status='pending'
            )
            self.stdout.write(f"\n✓ Pending requests visible to {manager.first_name}: {visible_requests.count()}")
            for req in visible_requests:
                self.stdout.write(f"  - Client: {req.loan.borrower}")
                self.stdout.write(f"    Amount: K{req.requested_amount}")
                self.stdout.write(f"    Officer: {req.requested_by}")

        self.stdout.write("\n=== DEBUG COMPLETE ===")