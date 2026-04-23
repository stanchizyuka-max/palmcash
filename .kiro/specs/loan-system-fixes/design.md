# Loan System Fixes Bugfix Design

## Overview

This design addresses three critical defects in the loan management system:

1. **Missing Application Review Link**: Managers and loan officers cannot navigate directly from a borrower's user detail page to their loan application, requiring manual navigation
2. **Loan Type Auto-Selection Not Working**: When users select "Daily" loan type, the Duration (21 weeks) and Days (56 days) fields are not auto-populated as expected
3. **Expense Not Deducting from Vault**: When expenses are recorded, the vault balance is not updated to reflect the deduction

The fix strategy involves:
- Adding a navigation link/button on the user detail page to access loan applications
- Fixing the JavaScript event listener to properly auto-populate loan term fields for Daily loans
- Ensuring the expense creation flow properly deducts amounts from the vault balance

## Glossary

- **Bug_Condition (C)**: The conditions that trigger each of the three bugs
- **Property (P)**: The desired correct behavior for each bug condition
- **Preservation**: Existing functionality that must remain unchanged by the fixes
- **UserDetailView**: The Django view in `accounts/views.py` that renders the user detail page at `/accounts/user/{id}/`
- **detail_tailwind.html**: The template file at `templates/clients/detail_tailwind.html` that displays user/client details
- **ExpenseCreateView**: The Django view in `expenses/views.py` that handles expense creation
- **BranchVault**: The model representing a branch's vault balance in `loans/models.py`
- **VaultTransaction**: The model in `expenses/models.py` that records vault transactions

## Bug Details

### Bug Condition

**Issue 1: Missing Application Review Link**

The bug manifests when a manager or loan officer views a borrower's user detail page. The template displays loan statistics and recent loan applications in a table, but does not provide a direct navigation link to view all applications or filter by that specific borrower.

**Formal Specification:**
```
FUNCTION isBugCondition_Issue1(input)
  INPUT: input of type PageView
  OUTPUT: boolean
  
  RETURN input.page == '/accounts/user/{id}/'
         AND input.user.role IN ['borrower']
         AND input.viewer.role IN ['manager', 'loan_officer', 'admin']
         AND NOT exists_link_to_loan_applications(input.page)
END FUNCTION
```

**Issue 2: Loan Type Auto-Selection Not Working**

The bug manifests when a user selects "Daily" as the loan type in the loan application form. The JavaScript change event listener should auto-populate the Duration and Days fields, but the current implementation does not set these values for Daily loan types.

**Formal Specification:**
```
FUNCTION isBugCondition_Issue2(input)
  INPUT: input of type FormInteraction
  OUTPUT: boolean
  
  RETURN input.field == 'loan_type'
         AND input.selected_value.name == 'Daily'
         AND input.selected_value.frequency == 'daily'
         AND (termInput.value == '' OR termInput.value == null)
END FUNCTION
```

**Issue 3: Expense Not Deducting from Vault**

The bug manifests when an expense is created through the ExpenseCreateView. The expense record is saved, but the vault balance deduction logic in the `form_valid` method has an error that prevents the vault balance from being updated.

**Formal Specification:**
```
FUNCTION isBugCondition_Issue3(input)
  INPUT: input of type ExpenseCreation
  OUTPUT: boolean
  
  RETURN input.action == 'create_expense'
         AND input.expense.amount > 0
         AND input.expense.branch IS NOT NULL
         AND vault_balance_not_updated(input.expense.branch, input.expense.amount)
END FUNCTION
```

### Examples

**Issue 1 Examples:**
- Manager views borrower John Doe's detail page at `/accounts/user/42/` → No link to view John's loan applications
- Loan officer views borrower Jane Smith's detail page → Must manually navigate to `/loans/applications/` and search for Jane
- Admin views borrower profile with 3 active loans → Can see loan table but no "View All Applications" button

**Issue 2 Examples:**
- User selects "Daily" loan type → Duration field remains empty (expected: 21 weeks auto-filled)
- User selects "Daily" loan type → Days field remains empty (expected: 56 days auto-filled)
- User selects "Weekly" loan type → Fields auto-populate correctly (existing behavior works)
- User manually enters term after selecting Daily → Manual entry should be preserved

**Issue 3 Examples:**
- Manager creates expense of K500 for "Office Supplies" → Expense saved but vault balance unchanged
- Admin records expense of K1000 for "Fuel" → VaultTransaction created but vault.balance not decremented
- Branch vault has K10,000, expense of K200 recorded → Vault still shows K10,000 instead of K9,800

## Expected Behavior

### Preservation Requirements

**Issue 1: Missing Application Review Link**

**Unchanged Behaviors:**
- All existing links and buttons on the user detail page must continue to function
- The loan statistics display (total loans, active loans, pending loans) must remain unchanged
- The recent loans table display must continue to show loan data correctly
- Navigation to individual loan detail pages via the "View" button in the table must continue to work

**Scope:**
All user detail page functionality that does not involve navigating to loan applications should be completely unaffected by this fix. This includes:
- Profile information display
- Document verification actions
- Loan officer assignment functionality
- Group membership display
- All other navigation links

**Issue 2: Loan Type Auto-Selection Not Working**

**Unchanged Behaviors:**
- Auto-population for Weekly loan types must continue to work as before
- Manual entry of Duration/Days fields must continue to be accepted and saved
- Loan calculator must continue to update correctly when fields change
- Form validation must continue to work for all loan types
- Loan type information card display must remain unchanged

**Scope:**
All loan application form functionality for non-Daily loan types should be completely unaffected by this fix. This includes:
- Weekly loan type auto-population
- Loan amount input and validation
- Purpose field functionality
- Form submission and validation
- Calculator display and calculations

**Issue 3: Expense Not Deducting from Vault**

**Unchanged Behaviors:**
- Expense record creation must continue to save all expense details correctly
- VaultTransaction record creation must continue to work
- Expense list view and filtering must remain unchanged
- Expense update and delete operations must continue to work
- Other vault operations (deposits, withdrawals, transfers) must remain unaffected

**Scope:**
All vault operations that do NOT involve expense creation should be completely unaffected by this fix. This includes:
- Capital injection transactions
- Bank withdrawal transactions
- Fund deposit transactions
- Branch transfer transactions
- Payment collection transactions
- Month close/open operations

## Hypothesized Root Cause

**Issue 1: Missing Application Review Link**

Based on the template analysis, the most likely issue is:

1. **Template Omission**: The `templates/clients/detail_tailwind.html` template displays recent loan applications in a table but does not include a link or button to view all applications for that borrower
   - The template shows a "Recent Loan Applications" section with a table
   - Each loan has a "View" button that links to individual loan details
   - Missing: A "View All Applications" button or link that navigates to the loan applications list filtered by this borrower

**Issue 2: Loan Type Auto-Selection Not Working**

Based on the JavaScript code in `templates/loans/apply.html`, the most likely issues are:

1. **Missing Auto-Population Logic**: The `loanTypeSelect.addEventListener('change')` function updates the term input attributes (min, max, placeholder) but does not actually SET the term input value
   - Lines 360-375 update the label, min/max attributes, and help text
   - Missing: `termInput.value = data.min_term_days` or similar assignment for Daily loans

2. **Incorrect Field Mapping**: The form may expect separate "duration" (weeks) and "days" fields, but the JavaScript only updates a single "term-input" field

**Issue 3: Expense Not Deducting from Vault**

Based on the `expenses/views.py` code analysis, the most likely issue is:

1. **Exception Handling Silencing Errors**: The `form_valid` method in `ExpenseCreateView` (lines 52-73) wraps the vault deduction logic in a try-except block that only prints errors without re-raising them
   - The vault deduction code exists (lines 54-73)
   - If any exception occurs, it's caught and printed but the form submission succeeds
   - Possible causes: Branch name mismatch, vault not found, save() failure

2. **Branch Name Case Sensitivity**: The code uses `Branch.objects.filter(name__iexact=expense.branch).first()` which should handle case, but if the expense.branch value doesn't match any branch name, the vault won't be found

3. **Transaction Atomicity**: The expense is saved before the vault deduction, so if the vault update fails, the expense still exists without the corresponding vault deduction

## Correctness Properties

Property 1: Bug Condition - Application Review Link Navigation

_For any_ page view where a manager or loan officer views a borrower's user detail page, the fixed template SHALL display a link or button that navigates to the loan applications list, allowing direct access to review the borrower's applications.

**Validates: Requirements 2.1, 2.2**

Property 2: Bug Condition - Daily Loan Auto-Population

_For any_ loan application form interaction where the user selects "Daily" as the loan type, the fixed JavaScript SHALL automatically populate the Duration field with 21 weeks and the Days field with 56 days (or the appropriate term value based on the loan type configuration).

**Validates: Requirements 2.3, 2.4**

Property 3: Bug Condition - Expense Vault Deduction

_For any_ expense creation where the expense amount is greater than zero and a valid branch is specified, the fixed ExpenseCreateView SHALL deduct the expense amount from the branch vault balance and create a corresponding VaultTransaction record.

**Validates: Requirements 2.5, 2.6**

Property 4: Preservation - User Detail Page Functionality

_For any_ user detail page interaction that does NOT involve navigating to loan applications (such as viewing profile info, assigning officers, or viewing individual loan details), the fixed template SHALL produce exactly the same behavior as the original template, preserving all existing navigation and display functionality.

**Validates: Requirements 3.1, 3.2**

Property 5: Preservation - Non-Daily Loan Type Behavior

_For any_ loan application form interaction where the user selects a loan type OTHER than "Daily" (such as Weekly), the fixed JavaScript SHALL produce exactly the same auto-population behavior as the original code, preserving existing functionality for other loan types.

**Validates: Requirements 3.3, 3.4, 3.5**

Property 6: Preservation - Non-Expense Vault Operations

_For any_ vault operation that is NOT an expense creation (such as deposits, withdrawals, transfers, or month close operations), the fixed code SHALL produce exactly the same vault balance updates as the original code, preserving all existing vault transaction functionality.

**Validates: Requirements 3.6, 3.7, 3.8**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**Issue 1: Missing Application Review Link**

**File**: `templates/clients/detail_tailwind.html`

**Location**: In the "Recent Loan Applications" section (around line 650)

**Specific Changes**:
1. **Add Navigation Button**: Add a "View All Applications" button in the header of the "Recent Loan Applications" section
   - Button should link to `/loans/applications/` with a query parameter to filter by borrower
   - Use consistent styling with other action buttons on the page
   - Place button next to the section title or in the section header

2. **Alternative Approach**: Add a link in the Quick Stats section
   - Add a clickable card or link that navigates to loan applications
   - Display total applications count as a clickable element

**Issue 2: Loan Type Auto-Selection Not Working**

**File**: `templates/loans/apply.html`

**Location**: JavaScript section, `loanTypeSelect.addEventListener('change')` function (around lines 351-380)

**Specific Changes**:
1. **Add Auto-Population for Daily Loans**: After updating the term input attributes for daily frequency, add code to set the default value
   - Add `termInput.value = data.min_term_days;` after line 368
   - This will auto-populate the Days field with 56 (or the configured min_term_days value)

2. **Add Auto-Population for Weekly Loans**: Similarly, add auto-population for weekly frequency
   - Add `termInput.value = data.min_term_weeks;` after line 375
   - This will auto-populate the Duration field with 21 (or the configured min_term_weeks value)

3. **Trigger Calculator Update**: After setting the value, trigger the calculateLoan() function
   - The function is already called at line 380, so this should work automatically

**Issue 3: Expense Not Deducting from Vault**

**File**: `expenses/views.py`

**Location**: `ExpenseCreateView.form_valid()` method (lines 44-73)

**Specific Changes**:
1. **Improve Error Handling**: Instead of silently catching exceptions, log them properly and show user feedback
   - Replace `print(f'Vault expense deduction error: {e}')` with proper logging
   - Add a warning message to the user if vault deduction fails
   - Consider making vault deduction mandatory (raise exception if it fails)

2. **Add Transaction Atomicity**: Wrap the entire operation in a database transaction
   - Use `@transaction.atomic` decorator or `with transaction.atomic():` block
   - Ensure expense save and vault deduction happen atomically
   - If vault deduction fails, rollback the expense creation

3. **Add Validation**: Before attempting vault deduction, validate that:
   - Branch exists and matches the expense.branch value
   - Vault has sufficient balance for the deduction
   - All required fields are present

4. **Fix Branch Lookup**: Ensure the branch name matching is robust
   - The current code uses `name__iexact` which should work
   - Add logging if branch is not found
   - Consider using branch ID instead of name for more reliable matching

5. **Move Vault Logic Before Super Call**: Move the vault deduction logic BEFORE `super().form_valid(form)` to ensure it happens before the success message
   - This allows proper error handling and prevents partial saves

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bugs on unfixed code, then verify the fixes work correctly and preserve existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fixes. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that simulate the bug conditions and assert the expected behavior. Run these tests on the UNFIXED code to observe failures and understand the root causes.

**Test Cases**:
1. **Issue 1 - Missing Link Test**: Load the user detail page for a borrower and check for presence of loan application navigation link (will fail on unfixed code)
2. **Issue 2 - Daily Auto-Population Test**: Simulate selecting "Daily" loan type and check if term field is auto-populated (will fail on unfixed code)
3. **Issue 3 - Vault Deduction Test**: Create an expense and verify vault balance is decremented (will fail on unfixed code)
4. **Edge Case - Non-Borrower User Detail**: Load user detail page for non-borrower (should not show loan section)

**Expected Counterexamples**:
- User detail page HTML does not contain a link with href matching `/loans/applications/`
- Term input field value remains empty after selecting Daily loan type
- Vault balance remains unchanged after expense creation
- Possible causes for Issue 3: Exception in vault deduction code, branch not found, transaction not committed

### Fix Checking

**Goal**: Verify that for all inputs where the bug conditions hold, the fixed code produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition_Issue1(input) DO
  result := render_user_detail_page_fixed(input)
  ASSERT contains_loan_application_link(result)
END FOR

FOR ALL input WHERE isBugCondition_Issue2(input) DO
  result := handle_loan_type_change_fixed(input)
  ASSERT termInput.value == expected_term_value(input.selected_value)
END FOR

FOR ALL input WHERE isBugCondition_Issue3(input) DO
  initial_balance := get_vault_balance(input.expense.branch)
  result := create_expense_fixed(input)
  final_balance := get_vault_balance(input.expense.branch)
  ASSERT final_balance == initial_balance - input.expense.amount
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug conditions do NOT hold, the fixed code produces the same result as the original code.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition_Issue1(input) DO
  ASSERT render_user_detail_page_original(input) = render_user_detail_page_fixed(input)
END FOR

FOR ALL input WHERE NOT isBugCondition_Issue2(input) DO
  ASSERT handle_loan_type_change_original(input) = handle_loan_type_change_fixed(input)
END FOR

FOR ALL input WHERE NOT isBugCondition_Issue3(input) DO
  ASSERT create_expense_original(input) = create_expense_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for non-bug scenarios, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Issue 1 Preservation**: Verify all other user detail page links (edit, assign officer, view individual loans) continue to work
2. **Issue 2 Preservation**: Verify Weekly loan type auto-population continues to work, manual term entry is preserved
3. **Issue 3 Preservation**: Verify other vault operations (deposits, withdrawals, transfers) continue to update vault balance correctly

### Unit Tests

**Issue 1: Missing Application Review Link**
- Test that user detail page for borrower contains loan application link
- Test that link has correct URL format (includes borrower filter parameter)
- Test that non-borrower user detail pages do not show loan application link
- Test that link is only visible to managers, loan officers, and admins

**Issue 2: Loan Type Auto-Selection Not Working**
- Test that selecting Daily loan type auto-populates term field with correct value
- Test that selecting Weekly loan type auto-populates term field with correct value
- Test that manually changing term field after auto-population preserves manual value
- Test that loan calculator updates correctly after auto-population

**Issue 3: Expense Not Deducting from Vault**
- Test that creating expense decrements vault balance by expense amount
- Test that VaultTransaction record is created with correct details
- Test that expense creation fails gracefully if vault not found
- Test that expense creation fails if vault has insufficient balance (if validation added)
- Test that transaction is atomic (expense not saved if vault deduction fails)

### Property-Based Tests

**Issue 1: Missing Application Review Link**
- Generate random borrower user IDs and verify link is present on all user detail pages
- Generate random viewer roles and verify link visibility matches role permissions
- Test that link URL correctly includes borrower ID parameter

**Issue 2: Loan Type Auto-Selection Not Working**
- Generate random loan type configurations and verify auto-population works for all frequencies
- Generate random term values and verify manual entry overrides auto-population
- Test that calculator updates correctly for all loan type and term combinations

**Issue 3: Expense Not Deducting from Vault**
- Generate random expense amounts and verify vault balance is always decremented correctly
- Generate random branch names and verify vault lookup works for all valid branches
- Test that vault balance is never negative after expense creation
- Test that VaultTransaction records always match vault balance changes

### Integration Tests

**Issue 1: Missing Application Review Link**
- Test full workflow: Navigate to user detail page → Click loan application link → Verify correct page loads
- Test that clicking link from different borrower pages loads correct filtered applications
- Test that link works for borrowers with no applications, one application, and multiple applications

**Issue 2: Loan Type Auto-Selection Not Working**
- Test full loan application workflow: Select Daily loan type → Verify auto-population → Submit form → Verify loan created with correct term
- Test that switching between loan types updates auto-population correctly
- Test that form validation works correctly with auto-populated values

**Issue 3: Expense Not Deducting from Vault**
- Test full expense workflow: Create expense → Verify vault balance updated → View vault transactions → Verify transaction recorded
- Test that multiple expenses in sequence correctly update vault balance
- Test that expense creation and vault deduction are atomic (rollback on failure)
- Test that vault balance displayed in UI reflects expense deductions
