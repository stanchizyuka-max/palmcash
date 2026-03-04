from django.core.management.base import BaseCommand
from loans.models import LoanType


class Command(BaseCommand):
    help = 'Update existing loan types to enforce 1-12 month term limits'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS(f'Updating loan type term limits (dry run: {dry_run})...')
        )
        
        loan_types = LoanType.objects.all()
        updated_count = 0
        
        for loan_type in loan_types:
            original_min = loan_type.min_term_months
            original_max = loan_type.max_term_months
            
            # Enforce 1-12 month limits
            new_min = max(1, min(loan_type.min_term_months, 12))
            new_max = max(1, min(loan_type.max_term_months, 12))
            
            # Ensure min is not greater than max
            if new_min > new_max:
                new_min = new_max
            
            if original_min != new_min or original_max != new_max:
                if not dry_run:
                    loan_type.min_term_months = new_min
                    loan_type.max_term_months = new_max
                    loan_type.save()
                
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'{"[DRY RUN] " if dry_run else ""}Updated {loan_type.name}: '
                        f'{original_min}-{original_max} months → {new_min}-{new_max} months'
                    )
                )
        
        if updated_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No loan types needed updating.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'{"DRY RUN: Would update" if dry_run else "Updated"} {updated_count} loan type(s).'
                )
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\nThis was a dry run. Use --dry-run=False to apply changes.'
                )
            )
