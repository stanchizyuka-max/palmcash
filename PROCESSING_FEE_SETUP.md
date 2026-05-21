# Processing Fee Setup Guide

## Overview
Processing fees can now be tracked as a separate transaction type in the vault system. This allows you to:
- Filter vault transactions by "Processing Fee"
- Track processing fee income separately
- Generate reports on processing fees collected

## What Was Done

### 1. Added Processing Fee Transaction Type
- Added 'processing_fee' to VaultTransaction model choices
- Updated vault filter dropdown to include "Processing Fee" option
- Created migration to update database schema

### 2. Created Identification Script
- Created `identify_processing_fees.py` script
- Script searches existing transactions for processing fee keywords
- Allows bulk relabeling of transactions as processing fees

## How to Use

### Step 1: Deploy Changes to Server

```bash
# On the server
cd ~/www/palmcashloans.site

# Pull latest changes
git pull origin main

# Run migration
python manage.py migrate

# Clear Python cache
find . -name "*.pyc" -delete

# Restart server
sudo systemctl restart gunicorn
```

### Step 2: Run the Identification Script

The script will search for transactions with these keywords in their description:
- 'processing fee'
- 'processing'
- 'fee'
- 'loan fee'
- 'application fee'
- 'admin fee'
- 'service fee'

```bash
# On the server
cd ~/www/palmcashloans.site
python identify_processing_fees.py
```

The script will:
1. Search all vault transactions for processing fee keywords
2. Show you all matching transactions
3. Ask for confirmation before relabeling
4. Update the transaction_type to 'processing_fee'

### Step 3: Verify in the System

1. Go to Dashboard → Branch Vault
2. In the "All Types" dropdown, select "Processing Fee"
3. Click "Filter"
4. You should now see all processing fee transactions

## Recording New Processing Fees

### Option 1: Manual Recording (Current Method)
When recording a processing fee in the vault:
1. Go to Branch Vault
2. Click "Inject Capital" or appropriate button
3. In the description, include "Processing Fee" or similar text
4. After recording, you can run the identification script to relabel it

### Option 2: Dedicated Button (Future Enhancement)
We can add a "Record Processing Fee" button that:
- Automatically sets transaction_type to 'processing_fee'
- Has a dedicated form for processing fees
- Links to the loan being processed

Would you like me to add this dedicated button?

## Troubleshooting

### Migration Error
If you see an error about missing migration dependencies:
```
NodeNotFoundError: Migration expenses.0015_add_processing_fee_type dependencies reference nonexistent parent node
```

**Solution**: The migration file has been fixed to reference the correct parent migration (0008). Pull the latest code and try again.

### No Processing Fees Found
If the script finds no processing fees:
1. Check if processing fees were recorded with different descriptions
2. Manually check "Cash Deposit" transactions around loan disbursement dates
3. Look for small amounts (typically K50-K200)
4. You may need to manually update transaction types in Django admin

### Filter Shows K0.00
If the Processing Fee filter shows K0.00:
1. Make sure you've run the identification script
2. Check that transactions were actually relabeled (check Django admin)
3. Clear browser cache and refresh the page

## Technical Details

### Database Changes
- Modified `VaultTransaction.transaction_type` field
- Added 'processing_fee' choice with display name "Processing Fee"
- Migration: `expenses/migrations/0015_add_processing_fee_type.py`

### Files Modified
- `expenses/models.py` - Added processing_fee to TRANSACTION_TYPE_CHOICES
- `dashboard/vault_views.py` - Added processing_fee to filter dropdown
- `identify_processing_fees.py` - Script to find and relabel transactions

### Search Logic
The script searches the `description` field (not `notes`) using case-insensitive matching:
```python
VaultTransaction.objects.filter(
    description__icontains=pattern
).exclude(
    transaction_type='processing_fee'
)
```

## Next Steps

1. **Deploy to server** - Pull changes and run migration
2. **Run identification script** - Find and relabel existing processing fees
3. **Verify filtering works** - Check vault history with Processing Fee filter
4. **Consider dedicated button** - Let me know if you want a "Record Processing Fee" button

## Questions?

If you need help with:
- Running the script
- Adding a dedicated processing fee button
- Generating processing fee reports
- Any other processing fee related features

Just let me know!
