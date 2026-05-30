#!/bin/bash
# Fix all current issues

echo "=========================================="
echo "FIXING ALL ISSUES"
echo "=========================================="
echo ""

# Issue 1: Fix loan LV-000088 payment schedules
echo "1. Fixing loan LV-000088 payment schedules..."
python fix_loan_lv000088_schedules.py
echo ""

# Issue 2: Inject capital to fix Chazanga negative vault
echo "2. Injecting capital to fix Chazanga vault..."
python manage.py shell << 'EOF'
from clients.models import Branch
from loans.vault_services import record_capital_injection
from accounts.models import User

branch = Branch.objects.get(name__iexact="chazanga")
admin = User.objects.filter(role="admin").first()

print(f"Current vault balance: {branch}")
vault_tx = record_capital_injection(branch, 19.81, "Correction for negative balance", admin, vault_type="weekly")
print(f"✅ Capital injection completed: {vault_tx}")
print(f"New balance should be K0.00")
EOF

echo ""
echo "=========================================="
echo "ALL FIXES COMPLETE"
echo "=========================================="
echo ""
echo "Please verify:"
echo "1. Loan LV-000088 shows only 1 payment made (not 2)"
echo "2. Chazanga vault balance is K0.00 (not negative)"
