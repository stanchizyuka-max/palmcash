"""
Management command to clean up duplicate month closing transactions.
Keeps only the first closing for each month and removes duplicates.
"""
from django.core.management.base import BaseCommand
from expenses.models import VaultTransaction
from collections import defaultdict


class Command(BaseCommand):
    help = 'Remove duplicate month closing transactions, keeping only the first one for each month'

    def add_arguments(self, parser):
        parser.add_argument(
            '--branch',
            type=str,
            help='Branch name to clean up (optional, cleans all branches if not specified)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        branch_filter = options.get('branch')
        dry_run = options.get('dry_run', False)

        # Get all month closing transactions
        closings = VaultTransaction.objects.filter(
            transaction_type='month_close'
        ).order_by('branch', 'transaction_date')

        if branch_filter:
            closings = closings.filter(branch=branch_filter)

        # Group by branch and month
        closings_by_branch_month = defaultdict(list)
        
        for closing in closings:
            # Extract month from description
            import re
            month_match = re.search(r'Month closing — ([\d-]+)', closing.description)
            if month_match:
                month = month_match.group(1)
                key = (closing.branch, month)
                closings_by_branch_month[key].append(closing)

        # Find and remove duplicates
        total_duplicates = 0
        
        for (branch, month), closing_list in closings_by_branch_month.items():
            if len(closing_list) > 1:
                # Keep the first one, delete the rest
                first_closing = closing_list[0]
                duplicates = closing_list[1:]
                
                self.stdout.write(
                    self.style.WARNING(
                        f'\nBranch: {branch}, Month: {month}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  KEEPING: {first_closing.reference_number} '
                        f'(K{first_closing.amount:,.2f}) '
                        f'at {first_closing.transaction_date}'
                    )
                )
                
                for dup in duplicates:
                    total_duplicates += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'  DELETING: {dup.reference_number} '
                            f'(K{dup.amount:,.2f}) '
                            f'at {dup.transaction_date}'
                        )
                    )
                    
                    if not dry_run:
                        dup.delete()

        if total_duplicates == 0:
            self.stdout.write(
                self.style.SUCCESS('\n✓ No duplicate closings found!')
            )
        else:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠ Found {total_duplicates} duplicate closing(s). '
                        f'Run without --dry-run to delete them.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Successfully deleted {total_duplicates} duplicate closing(s)!'
                    )
                )
