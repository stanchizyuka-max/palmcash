# Palm Cash - Unused Templates Cleanup Report

## Templates Safe to Delete

### 1. Empty Directories

#### `templates/location/`
- **Status**: EMPTY - No files
- **Action**: Delete this directory
- **Impact**: None

### 2. Unused Template Files

#### `templates/loans/list_tailwind.html`
- **Status**: UNUSED
- **Reason**: Not referenced in any views. `loans/list.html` is used instead
- **Action**: Delete this file
- **Impact**: None

#### `templates/loans/detail_simple.html`
- **Status**: UNUSED
- **Reason**: Not referenced in any views. `loans/detail.html` is used instead
- **Action**: Delete this file
- **Impact**: None

#### `templates/loans/detail_tailwind.html`
- **Status**: POTENTIALLY UNUSED
- **Reason**: Not directly referenced in loans views
- **Note**: Check if this is used elsewhere before deleting
- **Action**: Review usage, likely can be deleted

### 3. Duplicate/Old Templates

#### `templates/clients/detail.html` vs `templates/clients/detail_tailwind.html`
- **Status**: DUPLICATE
- **Reason**: `detail_tailwind.html` is used in `accounts/views.py` (UserDetailView)
- **Action**: Keep `detail_tailwind.html`, consider removing `detail.html` if not used
- **Note**: Verify `detail.html` is not used before deleting

#### `templates/reports/report_list.html` vs `templates/reports/report_list_tailwind.html`
- **Status**: DUPLICATE
- **Reason**: `report_list.html` is actively used, `report_list_tailwind.html` appears unused
- **Action**: Delete `report_list_tailwind.html` if not referenced
- **Impact**: None if not used

#### `templates/reports/system_statistics.html` vs `templates/reports/system_statistics_tailwind.html`
- **Status**: DUPLICATE
- **Reason**: `system_statistics_tailwind.html` is actively used
- **Action**: Delete `system_statistics.html` if not referenced
- **Impact**: None if not used

### 4. Legacy/Old Templates

#### `templates/loans/apply.html`
- **Status**: POTENTIALLY UNUSED
- **Reason**: `enhanced_apply.html` is used in views
- **Action**: Verify if `apply.html` is still needed, likely can be deleted

#### `templates/loans/edit.html`
- **Status**: POTENTIALLY UNUSED
- **Reason**: Not found in recent view references
- **Action**: Search for usage, delete if unused

#### `templates/clients/edit.html`
- **Status**: POTENTIALLY UNUSED
- **Reason**: Not found in recent view references
- **Action**: Search for usage, delete if unused

### 5. Admin Templates

#### `templates/admin/documents/` and `templates/admin/loans/`
- **Status**: REVIEW NEEDED
- **Reason**: These are Django admin customizations
- **Action**: Check if these directories have files and if they're needed
- **Impact**: May affect Django admin interface

## Templates Currently in Use (Keep These)

### Core Templates:
- ✅ `base_tailwind.html` - Base template for all pages
- ✅ `home_tailwind.html` - Home page

### Dashboard Templates:
- ✅ `dashboard/admin_dashboard.html`
- ✅ `dashboard/borrower_dashboard.html`
- ✅ `dashboard/pending_approvals.html`
- ✅ `dashboard/access_denied.html` (used in multiple views)

### Loan Templates (Active):
- ✅ `loans/list.html`
- ✅ `loans/detail.html`
- ✅ `loans/enhanced_apply.html`
- ✅ `loans/submit_application.html`
- ✅ `loans/applications_list.html`
- ✅ `loans/approve_application.html`
- ✅ `loans/application_detail_view.html`
- ✅ `loans/select_borrower.html`
- ✅ `loans/borrower_detail_for_application.html`
- ✅ `loans/hierarchical.html`
- ✅ `loans/upfront_payment.html`
- ✅ `loans/calculator.html`
- ✅ `loans/status_dashboard.html`
- ✅ `loans/document_review_dashboard.html`
- ✅ `loans/loan_types_manage.html`
- ✅ `loans/loan_documents_manage.html`

### Payment Templates (Active):
- ✅ `payments/list.html`
- ✅ `payments/detail.html`
- ✅ `payments/make.html`
- ✅ `payments/schedule.html`
- ✅ `payments/bulk_collection.html`
- ✅ `payments/bulk_collection_group.html`
- ✅ `payments/default_collection.html`
- ✅ `payments/default_collection_group.html`
- ✅ `payments/default_collection_history.html`
- ✅ `payments/collection_history.html`
- ✅ `payments/collections_history.html`
- ✅ `payments/securities_history.html`
- ✅ `payments/history.html`
- ✅ `payments/hierarchical.html`
- ✅ `payments/upfront_payment.html`

### Client Templates (Active):
- ✅ `clients/list.html`
- ✅ `clients/detail_tailwind.html`
- ✅ `clients/group_list.html`
- ✅ `clients/group_detail.html`
- ✅ `clients/register_borrower_wizard.html`
- ✅ `clients/drilldown.html`

### Securities Templates (Active):
- ✅ `securities/branch_summary.html`
- ✅ `securities/officer_summary.html`
- ✅ `securities/officer_groups.html`
- ✅ `securities/group_clients.html`
- ✅ `securities/client_detail.html`

### Report Templates (Active):
- ✅ `reports/report_list.html`
- ✅ `reports/system_statistics_tailwind.html`
- ✅ `reports/loan_report.html`
- ✅ `reports/payment_report.html`
- ✅ `reports/financial_report.html`
- ✅ `reports/monthly_collection_trend.html`

### Message Templates (Active):
- ✅ `messages/inbox.html`
- ✅ `messages/sent.html`
- ✅ `messages/detail.html`
- ✅ `messages/threads.html`

### Notification Templates (Active):
- ✅ `notifications/list.html`
- ✅ `notifications/detail.html`

### Pages Templates (Active):
- ✅ `pages/about.html`
- ✅ `pages/contact.html`
- ✅ `pages/terms.html`

### Payroll Templates (Active):
- ✅ `payroll/dashboard.html`
- ✅ All other payroll templates (actively used)

## Cleanup Commands

### Safe to Delete Immediately:
```bash
# Delete empty directory
Remove-Item -Recurse -Force templates/location

# Delete unused loan templates
Remove-Item templates/loans/list_tailwind.html
Remove-Item templates/loans/detail_simple.html

# Delete unused report templates (after verification)
Remove-Item templates/reports/report_list_tailwind.html
Remove-Item templates/reports/system_statistics.html
```

### Requires Verification Before Deletion:
```bash
# Search for usage before deleting
# Check if these are referenced anywhere
grep -r "detail_tailwind" --include="*.html" templates/
grep -r "apply.html" --include="*.py" .
grep -r "edit.html" --include="*.py" .
```

## Recommendations

### 1. Template Naming Convention
- Standardize on either `_tailwind` suffix or no suffix
- Current mix is confusing (some have `_tailwind`, some don't)
- Recommendation: Remove `_tailwind` suffix since all templates use Tailwind now

### 2. Template Organization
- Consider moving app-specific templates to app directories
  - Example: Move `templates/loans/` to `loans/templates/loans/`
  - This follows Django best practices

### 3. Duplicate Template Cleanup
- Identify and remove all duplicate templates
- Keep only the actively used version
- Update any references to point to the correct template

### 4. Email Templates
- All email templates in `templates/emails/` appear to be in use
- Keep these for notification system

### 5. Admin Templates
- Review `templates/admin/` customizations
- Remove if not needed or consolidate

## Impact Assessment

### Low Risk (Safe to Delete Now):
- ✅ `templates/location/` (empty directory)
- ✅ `templates/loans/list_tailwind.html` (not referenced)
- ✅ `templates/loans/detail_simple.html` (not referenced)

### Medium Risk (Verify First):
- ⚠️ `templates/reports/report_list_tailwind.html`
- ⚠️ `templates/reports/system_statistics.html`
- ⚠️ `templates/loans/apply.html`
- ⚠️ `templates/loans/edit.html`
- ⚠️ `templates/clients/detail.html`
- ⚠️ `templates/clients/edit.html`

### High Risk (Keep for Now):
- ⛔ All actively used templates listed above
- ⛔ Email templates (used by notification system)
- ⛔ Admin templates (may affect Django admin)

## Next Steps

1. **Immediate**: Delete low-risk templates
2. **This Week**: Verify medium-risk templates and delete if unused
3. **This Month**: Standardize template naming convention
4. **Ongoing**: Keep templates organized and documented
