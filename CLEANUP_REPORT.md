# Palm Cash - Unused Code Cleanup Report

## Files Safe to Delete

### 1. Root Directory Files

#### `context_processors.py` (Root)
- **Status**: UNUSED
- **Reason**: Settings.py uses `common.context_processors.unread_notifications` instead
- **Action**: Delete this file
- **Impact**: None - functionality is duplicated in `common/context_processors.py`

#### `index.html` (Root)
- **Status**: UNUSED
- **Reason**: This is a placeholder "Hello World" page from ISPManager, not part of the Django application
- **Action**: Delete this file
- **Impact**: None - Django serves its own templates

### 2. Unused Directories

#### `palmcash-env/`
- **Status**: UNUSED/DUPLICATE
- **Reason**: This appears to be an old virtual environment. The active one is `.venv/`
- **Action**: Delete this directory
- **Impact**: None - `.venv/` is the active virtual environment
- **Note**: Make sure `.venv/` is working before deleting

#### `webstat/`
- **Status**: UNUSED
- **Reason**: Contains only `index.html`, not referenced anywhere in the codebase
- **Action**: Delete this directory
- **Impact**: None - not part of the application

### 3. Database Files

#### `palmcash_db.sql`
- **Status**: BACKUP/ARCHIVE
- **Reason**: SQL dump file in root directory
- **Action**: Move to a `backups/` folder or delete if you have proper backups elsewhere
- **Impact**: None on running application
- **Recommendation**: Keep in a dedicated backups folder, not in project root

## Potentially Unused Django Apps

### Apps to Review:

#### `pages` app
- **Registered**: Yes (in INSTALLED_APPS)
- **Usage**: Check if this app is actually being used
- **Files**: Very minimal - only has basic Django app structure
- **Action**: Review if needed, consider removing if unused

#### `internal_messages` app
- **Registered**: Yes (in INSTALLED_APPS)
- **Usage**: Check if this is being used vs the `notifications` app
- **Potential Duplication**: May overlap with `notifications` app
- **Action**: Review usage and consider consolidating

## Deprecated/Legacy Code Patterns

### 1. Loan Model - Monthly Fields (DEPRECATED)
**Location**: `loans/models.py`

```python
# Legacy monthly fields (deprecated)
max_term_months = models.IntegerField(
    null=True,
    blank=True,
    help_text="DEPRECATED: No longer used"
)
min_term_months = models.IntegerField(
    null=True,
    blank=True,
    help_text="DEPRECATED: No longer used"
)
```

**Action**: These fields are marked as deprecated but still in the model. Consider:
1. Creating a migration to remove them (after ensuring no data depends on them)
2. Or keep them for historical data but document clearly

### 2. Loan Model - Monthly Payment Field (DEPRECATED)
**Location**: `loans/models.py`

```python
monthly_payment = models.DecimalField(
    max_digits=10, 
    decimal_places=2,
    null=True,
    blank=True,
    help_text="DEPRECATED: Use payment_amount instead"
)
```

**Action**: Same as above - consider removing after data migration

## Cleanup Commands

### Safe to Delete Immediately:
```bash
# Delete unused root files
rm context_processors.py
rm index.html

# Delete unused directories
rm -rf webstat/
rm -rf palmcash-env/  # Only after confirming .venv works

# Move database backup
mkdir -p backups
mv palmcash_db.sql backups/
```

### Requires Review Before Deletion:
```bash
# Review these apps for actual usage
# Check if 'pages' app is used
grep -r "pages" --include="*.py" --include="*.html" .

# Check if 'internal_messages' is used vs 'notifications'
grep -r "internal_messages" --include="*.py" --include="*.html" .
```

## Database Cleanup (Future)

### Deprecated Fields to Remove (After Data Migration):
1. `Loan.max_term_months`
2. `Loan.min_term_months`
3. `Loan.term_months`
4. `Loan.monthly_payment`
5. `LoanType.max_term_months`
6. `LoanType.min_term_months`

**Steps**:
1. Verify no data uses these fields
2. Create Django migration to remove fields
3. Run migration on development first
4. Test thoroughly
5. Deploy to production

## Recommendations

### 1. Code Organization
- Move all backup files to a dedicated `backups/` directory
- Keep only active virtual environment (`.venv/`)
- Remove placeholder files from hosting provider

### 2. App Consolidation
- Review if `internal_messages` and `notifications` can be consolidated
- Review if `pages` app is necessary or can be merged into `common`

### 3. Model Cleanup
- Plan migration to remove deprecated fields
- Document which fields are legacy vs active
- Add database indexes where needed for performance

### 4. Git Cleanup
- Add unused directories to `.gitignore`
- Remove tracked files that shouldn't be in version control

## Impact Assessment

### Low Risk (Safe to Delete Now):
- ✅ `context_processors.py` (root)
- ✅ `index.html` (root)
- ✅ `webstat/` directory
- ✅ `palmcash-env/` directory (after verification)

### Medium Risk (Review First):
- ⚠️ `pages` app
- ⚠️ `internal_messages` app
- ⚠️ Deprecated model fields

### High Risk (Requires Migration):
- ⛔ Removing deprecated database fields (needs proper migration)

## Next Steps

1. **Immediate**: Delete low-risk files
2. **This Week**: Review medium-risk apps for usage
3. **This Month**: Plan migration for deprecated fields
4. **Ongoing**: Keep codebase clean and documented
