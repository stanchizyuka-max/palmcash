# Bugfix Requirements Document

## Introduction

This document addresses three critical defects in the loan management system that impact manager workflow efficiency, loan application data accuracy, and financial record integrity. These issues affect the user detail page navigation, loan application form auto-population, and expense tracking functionality.

## Bug Analysis

### Current Behavior (Defect)

**Issue 1: Missing Application Review Link**

1.1 WHEN a manager views the manager dashboard THEN the system displays a "Loan Applications Review" section with links to /loans/applications_list/ but the link may not be working correctly or is not prominently displayed for easy access

1.2 WHEN a manager needs to review borrower loan applications from the dashboard THEN the system should provide clear, working navigation to the loan applications list at /loans/applications/

**Issue 2: Loan Type Auto-Selection Not Working**

1.3 WHEN a user selects "Daily" as the loan type in the loan application form THEN the system does not auto-populate the Duration field with 21 weeks

1.4 WHEN a user selects "Daily" as the loan type in the loan application form THEN the system does not auto-populate the Days field with 56 days

**Issue 3: Expense Not Deducting from Vault**

1.5 WHEN an expense is recorded in the system THEN the system records the expense but does not deduct the expense amount from the vault balance

1.6 WHEN the vault balance is checked after recording an expense THEN the system shows an incorrect balance that does not reflect the expense deduction

### Expected Behavior (Correct)

**Issue 1: Missing Application Review Link**

2.1 WHEN a manager views the manager dashboard THEN the system SHALL display a "Loan Applications Review" section with clear, working links that navigate to the loan applications list at /loans/applications/

2.2 WHEN a manager clicks the loan application review link from the dashboard THEN the system SHALL navigate to the correct loan applications page where they can review and approve applications

**Issue 2: Loan Type Auto-Selection Not Working**

2.3 WHEN a user selects "Daily" as the loan type in the loan application form THEN the system SHALL automatically populate the Duration field with 21 weeks

2.4 WHEN a user selects "Daily" as the loan type in the loan application form THEN the system SHALL automatically populate the Days field with 56 days

**Issue 3: Expense Not Deducting from Vault**

2.5 WHEN an expense is recorded in the system THEN the system SHALL deduct the expense amount from the vault balance

2.6 WHEN the vault balance is checked after recording an expense THEN the system SHALL display the updated balance reflecting the expense deduction

### Unchanged Behavior (Regression Prevention)

**Issue 1: Missing Application Review Link**

3.1 WHEN a manager accesses other sections of the manager dashboard THEN the system SHALL CONTINUE TO display all dashboard sections without errors

3.2 WHEN a manager accesses other navigation links on the dashboard THEN the system SHALL CONTINUE TO function as expected

**Issue 2: Loan Type Auto-Selection Not Working**

3.3 WHEN a user selects a loan type other than "Daily" in the loan application form THEN the system SHALL CONTINUE TO behave according to the existing rules for that loan type

3.4 WHEN a user manually enters or modifies the Duration or Days fields after auto-population THEN the system SHALL CONTINUE TO accept and save the manually entered values

3.5 WHEN a user submits a loan application with valid data THEN the system SHALL CONTINUE TO process and save the application correctly

**Issue 3: Expense Not Deducting from Vault**

3.6 WHEN other vault transactions (deposits, withdrawals, transfers) are recorded THEN the system SHALL CONTINUE TO update the vault balance correctly

3.7 WHEN an expense is viewed or listed THEN the system SHALL CONTINUE TO display the expense details correctly

3.8 WHEN vault balance is queried for reporting purposes THEN the system SHALL CONTINUE TO provide accurate balance information for all transaction types
