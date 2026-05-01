"""
Management command to migrate from single vault to dual-vault system.

This command:
1. Analyzes existing vault data
2. Creates DailyVault and WeeklyVault for each branch
3. Splits balances based on loan types
4. Migrates transaction history
5. Validates data integrity

Usage:
    python manage.py migrate_to_dual_vault --analyze  # Dry run analysis
    python manage.py migrate_to_dual_vault --migrate  # Execute migration
    python manage.py migrate_to_dual_vault --validate # Validate after migration
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum, Q, Count
from decimal import Decimal
from loans.models import Loan, BranchVault, DailyVault, WeeklyVault
from expenses.models import VaultTransaction
from clients.models import Branch
from payments.models import Payment


class Command(BaseCommand):
    help = 'Migrate from single vault to dual-vault system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze current data without making changes',
        )
        parser.add_argument(
            '--migrate',
            action='store_true',
            help='Execute the migration',
        )
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Validate migration results',
        )
        parser.add_argument(
            '--branch',
            type=str,
            help='Migrate specific branch only',
        )

    def handle(self, *args, **options):
        if options['analyze']:
            self.analyze_data()
        elif options['migrate']:
            branch_name = options.get('branch')
            self.execute_migration(branch_name)
        elif options['validate']:
            self.validate_migration()
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Please specify --analyze, --migrate, or --validate'
                )
            )

    def analyze_data(self):
        """Analyze current vault data and show migration plan"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('DUAL-VAULT MIGRATION ANALYSIS'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        branches = Branch.objects.filter(is_active=True)
        
        for branch in branches:
            self.stdout.write(f'\n{"-"*70}')
            self.stdout.write(f'Branch: {branch.name}')
            self.stdout.write(f'{"-"*70}')
            
            # Get legacy vault
            try:
                legacy_vault = BranchVault.objects.get(branch=branch)
                current_balance = legacy_vault.balance
                self.stdout.write(f'Current Vault Balance: K{current_balance:,.2f}')
            except BranchVault.DoesNotExist:
                self.stdout.write(self.style.WARNING('  No legacy vault found'))
                continue
            
            # Analyze loans by type
            daily_loans = Loan.objects.filter(
                loan_officer__officer_assignment__branch=branch.name,
                repayment_frequency='daily'
            )
            weekly_loans = Loan.objects.filter(
                loan_officer__officer_assignment__branch=branch.name,
                repayment_frequency='weekly'
            )
            
            self.stdout.write(f'\nLoan Analysis:')
            self.stdout.write(f'  Daily Loans: {daily_loans.count()}')
            self.stdout.write(f'  Weekly Loans: {weekly_loans.count()}')
            
            # Calculate disbursements
            daily_disbursed = daily_loans.filter(
                status__in=['active', 'completed', 'disbursed']
            ).aggregate(total=Sum('principal_amount'))['total'] or Decimal('0')
            
            weekly_disbursed = weekly_loans.filter(
                status__in=['active', 'completed', 'disbursed']
            ).aggregate(total=Sum('principal_amount'))['total'] or Decimal('0')
            
            self.stdout.write(f'\nDisbursements:')
            self.stdout.write(f'  Daily: K{daily_disbursed:,.2f}')
            self.stdout.write(f'  Weekly: K{weekly_disbursed:,.2f}')
            self.stdout.write(f'  Total: K{(daily_disbursed + weekly_disbursed):,.2f}')
            
            # Calculate collections
            daily_collected = Payment.objects.filter(
                loan__in=daily_loans,
                status='confirmed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            weekly_collected = Payment.objects.filter(
                loan__in=weekly_loans,
                status='confirmed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            self.stdout.write(f'\nCollections:')
            self.stdout.write(f'  Daily: K{daily_collected:,.2f}')
            self.stdout.write(f'  Weekly: K{weekly_collected:,.2f}')
            self.stdout.write(f'  Total: K{(daily_collected + weekly_collected):,.2f}')
            
            # Calculate net positions
            daily_net = daily_collected - daily_disbursed
            weekly_net = weekly_collected - weekly_disbursed
            
            self.stdout.write(f'\nNet Position (Collections - Disbursements):')
            self.stdout.write(f'  Daily: K{daily_net:,.2f}')
            self.stdout.write(f'  Weekly: K{weekly_net:,.2f}')
            
            # Proposed split
            total_disbursed = daily_disbursed + weekly_disbursed
            if total_disbursed > 0:
                daily_ratio = daily_disbursed / total_disbursed
                weekly_ratio = weekly_disbursed / total_disbursed
                
                proposed_daily = current_balance * daily_ratio
                proposed_weekly = current_balance * weekly_ratio
            else:
                # No loans yet, split 50/50
                proposed_daily = current_balance / 2
                proposed_weekly = current_balance / 2
            
            self.stdout.write(f'\nProposed Vault Split:')
            self.stdout.write(f'  Daily Vault: K{proposed_daily:,.2f}')
            self.stdout.write(f'  Weekly Vault: K{proposed_weekly:,.2f}')
            self.stdout.write(f'  Total: K{(proposed_daily + proposed_weekly):,.2f}')
            
            # Analyze transactions
            vault_txns = VaultTransaction.objects.filter(branch=branch.name)
            self.stdout.write(f'\nVault Transactions:')
            self.stdout.write(f'  Total: {vault_txns.count()}')
            
            # Transactions with loans
            daily_txns = vault_txns.filter(
                loan__repayment_frequency='daily'
            ).count()
            weekly_txns = vault_txns.filter(
                loan__repayment_frequency='weekly'
            ).count()
            no_loan_txns = vault_txns.filter(loan__isnull=True).count()
            
            self.stdout.write(f'  Daily loan transactions: {daily_txns}')
            self.stdout.write(f'  Weekly loan transactions: {weekly_txns}')
            self.stdout.write(f'  Non-loan transactions: {no_loan_txns}')
        
        self.stdout.write(f'\n{"="*70}')
        self.stdout.write(self.style.SUCCESS('Analysis complete!'))
        self.stdout.write(self.style.WARNING('\nTo proceed with migration, run:'))
        self.stdout.write(self.style.WARNING('  python manage.py migrate_to_dual_vault --migrate'))
        self.stdout.write(f'{"="*70}\n')

    @transaction.atomic
    def execute_migration(self, branch_name=None):
        """Execute the actual migration"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('EXECUTING DUAL-VAULT MIGRATION'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        if branch_name:
            branches = Branch.objects.filter(name=branch_name, is_active=True)
            if not branches.exists():
                self.stdout.write(self.style.ERROR(f'Branch "{branch_name}" not found'))
                return
        else:
            branches = Branch.objects.filter(is_active=True)
        
        for branch in branches:
            self.stdout.write(f'\nMigrating branch: {branch.name}')
            
            try:
                legacy_vault = BranchVault.objects.get(branch=branch)
            except BranchVault.DoesNotExist:
                self.stdout.write(self.style.WARNING('  No legacy vault - creating new vaults with K0'))
                legacy_vault = None
            
            # Create or get daily vault
            daily_vault, created = DailyVault.objects.get_or_create(
                branch=branch,
                defaults={'balance': Decimal('0')}
            )
            if created:
                self.stdout.write('  ✓ Created Daily Vault')
            
            # Create or get weekly vault
            weekly_vault, created = WeeklyVault.objects.get_or_create(
                branch=branch,
                defaults={'balance': Decimal('0')}
            )
            if created:
                self.stdout.write('  ✓ Created Weekly Vault')
            
            if legacy_vault:
                # Calculate split
                daily_loans = Loan.objects.filter(
                    loan_officer__officer_assignment__branch=branch.name,
                    repayment_frequency='daily',
                    status__in=['active', 'completed', 'disbursed']
                )
                weekly_loans = Loan.objects.filter(
                    loan_officer__officer_assignment__branch=branch.name,
                    repayment_frequency='weekly',
                    status__in=['active', 'completed', 'disbursed']
                )
                
                daily_disbursed = daily_loans.aggregate(
                    total=Sum('principal_amount')
                )['total'] or Decimal('0')
                weekly_disbursed = weekly_loans.aggregate(
                    total=Sum('principal_amount')
                )['total'] or Decimal('0')
                
                total_disbursed = daily_disbursed + weekly_disbursed
                
                if total_disbursed > 0:
                    daily_ratio = daily_disbursed / total_disbursed
                    daily_vault.balance = legacy_vault.balance * daily_ratio
                    weekly_vault.balance = legacy_vault.balance * (Decimal('1') - daily_ratio)
                else:
                    # Split 50/50 if no loans
                    daily_vault.balance = legacy_vault.balance / 2
                    weekly_vault.balance = legacy_vault.balance / 2
                
                daily_vault.save()
                weekly_vault.save()
                
                self.stdout.write(f'  ✓ Split balance: Daily=K{daily_vault.balance:,.2f}, Weekly=K{weekly_vault.balance:,.2f}')
                
                # Mark legacy vault as migrated
                legacy_vault.is_migrated = True
                legacy_vault.save()
            
            # Migrate transactions
            self.migrate_transactions(branch)
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('Migration completed successfully!'))
        self.stdout.write(self.style.WARNING('\nRun validation:'))
        self.stdout.write(self.style.WARNING('  python manage.py migrate_to_dual_vault --validate'))
        self.stdout.write('='*70 + '\n')

    def migrate_transactions(self, branch):
        """Migrate vault transactions to include vault_type"""
        vault_txns = VaultTransaction.objects.filter(
            branch=branch.name,
            vault_type__isnull=True
        )
        
        updated = 0
        for txn in vault_txns:
            if txn.loan:
                # Assign based on loan type
                txn.vault_type = txn.loan.repayment_frequency
                txn.save(update_fields=['vault_type'])
                updated += 1
            else:
                # Non-loan transactions - assign to weekly by default
                # (can be manually adjusted later)
                txn.vault_type = 'weekly'
                txn.save(update_fields=['vault_type'])
                updated += 1
        
        if updated > 0:
            self.stdout.write(f'  ✓ Updated {updated} transactions with vault_type')

    def validate_migration(self):
        """Validate migration results"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('VALIDATING DUAL-VAULT MIGRATION'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        branches = Branch.objects.filter(is_active=True)
        all_valid = True
        
        for branch in branches:
            self.stdout.write(f'\nValidating: {branch.name}')
            
            # Check vaults exist
            try:
                daily_vault = DailyVault.objects.get(branch=branch)
                weekly_vault = WeeklyVault.objects.get(branch=branch)
                self.stdout.write('  ✓ Both vaults exist')
            except (DailyVault.DoesNotExist, WeeklyVault.DoesNotExist):
                self.stdout.write(self.style.ERROR('  ✗ Missing vaults'))
                all_valid = False
                continue
            
            # Check legacy vault
            try:
                legacy_vault = BranchVault.objects.get(branch=branch)
                if not legacy_vault.is_migrated:
                    self.stdout.write(self.style.WARNING('  ⚠ Legacy vault not marked as migrated'))
                
                # Validate balance split
                total_new = daily_vault.balance + weekly_vault.balance
                diff = abs(legacy_vault.balance - total_new)
                if diff < Decimal('0.01'):  # Allow 1 cent rounding difference
                    self.stdout.write(f'  ✓ Balance reconciled: K{legacy_vault.balance:,.2f} = K{total_new:,.2f}')
                else:
                    self.stdout.write(self.style.ERROR(
                        f'  ✗ Balance mismatch: Legacy=K{legacy_vault.balance:,.2f}, New=K{total_new:,.2f}, Diff=K{diff:,.2f}'
                    ))
                    all_valid = False
            except BranchVault.DoesNotExist:
                self.stdout.write('  ℹ No legacy vault to compare')
            
            # Check transactions
            total_txns = VaultTransaction.objects.filter(branch=branch.name).count()
            typed_txns = VaultTransaction.objects.filter(
                branch=branch.name,
                vault_type__isnull=False
            ).count()
            
            if total_txns == typed_txns:
                self.stdout.write(f'  ✓ All {total_txns} transactions have vault_type')
            else:
                missing = total_txns - typed_txns
                self.stdout.write(self.style.ERROR(
                    f'  ✗ {missing} transactions missing vault_type'
                ))
                all_valid = False
        
        self.stdout.write('\n' + '='*70)
        if all_valid:
            self.stdout.write(self.style.SUCCESS('✓ Validation passed!'))
        else:
            self.stdout.write(self.style.ERROR('✗ Validation failed - please review errors above'))
        self.stdout.write('='*70 + '\n')
