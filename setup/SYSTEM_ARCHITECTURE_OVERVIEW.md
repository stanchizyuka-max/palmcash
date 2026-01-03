# PalmCash System Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PALMCASH LOAN MANAGEMENT SYSTEM                 │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                            USER INTERFACE LAYER                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  ADMIN PORTAL   │  │ MANAGER PORTAL  │  │ OFFICER PORTAL  │         │
│  │                 │  │                 │  │                 │         │
│  │ • Statistics    │  │ • Portfolio     │  │ • Groups        │         │
│  │ • Reports       │  │ • Expenses      │  │ • Loans         │         │
│  │ • Officers      │  │ • Vault         │  │ • Collections   │         │
│  │ • Deposits      │  │ • Reports       │  │ • Deposits      │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              BORROWER PORTAL                                    │   │
│  │  • Loan Application | Payment History | Loan Status            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LOGIC LAYER                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │  LOAN MANAGEMENT │  │ GROUP MANAGEMENT │  │ EXPENSE TRACKING │      │
│  │                  │  │                  │  │                  │      │
│  │ • Applications   │  │ • Create Groups  │  │ • Record Expense │      │
│  │ • Approvals      │  │ • Assign Members │  │ • Approve Expense│      │
│  │ • Disbursements  │  │ • Filter Groups  │  │ • Report Expense │      │
│  │ • Repayments     │  │ • Manage Members │  │ • Category Track │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │ DEPOSIT TRACKING │  │ VAULT MANAGEMENT │  │ REPORTING ENGINE │      │
│  │                  │  │                  │  │                  │      │
│  │ • Calculate 10%  │  │ • Record Trans.  │  │ • Daily Reports  │      │
│  │ • Record Payment │  │ • Branch Balance │  │ • P&L Dashboard  │      │
│  │ • Verify Deposit │  │ • Cash Tracking  │  │ • Collections    │      │
│  │ • Block Disburse │  │ • Transfers      │  │ • Expense Report │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              PERMISSION & VALIDATION ENGINE                      │   │
│  │  • Role-based access control                                    │   │
│  │  • Minimum 15 groups validation for loan approval               │   │
│  │  • Security deposit verification before disbursement            │   │
│  │  • Field validation and business rule enforcement               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                           DATA ACCESS LAYER                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │  USER MODELS     │  │  LOAN MODELS     │  │  GROUP MODELS    │      │
│  │                  │  │                  │  │                  │      │
│  │ • User           │  │ • Loan           │  │ • BorrowerGroup  │      │
│  │ • Role           │  │ • LoanType       │  │ • Borrower       │      │
│  │ • Permissions    │  │ • LoanDocument   │  │ • OfficerAssign  │      │
│  │ • Profile        │  │ • SecurityDeposit│  │ • GroupMember    │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │ PAYMENT MODELS   │  │ EXPENSE MODELS   │  │ TRANSACTION MODEL│      │
│  │                  │  │                  │  │                  │      │
│  │ • Payment        │  │ • Expense        │  │ • VaultTransaction
│  │ • PaymentSchedule│  │ • ExpenseCategory│  │ • BranchBalance  │      │
│  │ • PaymentMethod  │  │ • Approval       │  │ • TransactionType│      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                         DATABASE LAYER (MySQL)                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  PALMCASH_DB                                                    │   │
│  │                                                                 │   │
│  │  Tables:                                                        │   │
│  │  • accounts_user (Users with roles)                            │   │
│  │  • clients_borrowergroup (Groups with branch, payment_day)     │   │
│  │  • clients_borrower (Borrowers in groups)                      │   │
│  │  • loans_loan (Loans with daily/weekly repayment)              │   │
│  │  • loans_securitydeposit (10% deposits)                        │   │
│  │  • payments_payment (Payment records)                          │   │
│  │  • payments_paymentschedule (Payment schedules)                │   │
│  │  • expenses_expense (Operational expenses)                     │   │
│  │  • expenses_vaulttransaction (Cash movements)                  │   │
│  │  • clients_officerassignment (Officer workload)                │   │
│  │  • notifications_notification (System notifications)           │   │
│  │  • documents_document (Uploaded documents)                     │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Loan Approval & Disbursement Flow

```
BORROWER APPLIES FOR LOAN
        ↓
LOAN OFFICER REVIEWS
        ↓
CHECK: Officer has ≥15 active groups?
        ├─ NO → ❌ CANNOT APPROVE (Show error message)
        └─ YES → ✅ APPROVE LOAN
                    ↓
            SYSTEM CREATES SECURITY DEPOSIT RECORD
            (Amount = Principal × 10%)
                    ↓
            BORROWER PAYS SECURITY DEPOSIT
                    ↓
            LOAN OFFICER RECORDS DEPOSIT PAYMENT
                    ↓
            MANAGER VERIFIES DEPOSIT
                    ↓
            CHECK: Deposit verified?
                    ├─ NO → ❌ CANNOT DISBURSE (Show error)
                    └─ YES → ✅ DISBURSE LOAN
                                ↓
                        SYSTEM GENERATES PAYMENT SCHEDULE
                                ↓
                        LOAN STATUS = ACTIVE
                                ↓
                        BORROWER BEGINS REPAYMENT
```

### Expense Tracking Flow

```
MANAGER RECORDS EXPENSE
        ↓
SYSTEM VALIDATES:
├─ Category selected?
├─ Amount > 0?
├─ Date valid?
└─ Description provided?
        ↓
EXPENSE CREATED (Status = Pending)
        ↓
MANAGER/ADMIN REVIEWS EXPENSE
        ↓
APPROVE or REJECT?
        ├─ APPROVE → Status = Approved
        │            Recorded in financial reports
        │            Included in P&L calculations
        │
        └─ REJECT → Status = Rejected
                    Not included in reports
```

### Security Deposit Verification Flow

```
LOAN APPROVED
        ↓
SECURITY DEPOSIT REQUIRED (10% of principal)
        ↓
BORROWER PAYS DEPOSIT
        ↓
LOAN OFFICER RECORDS PAYMENT
        ├─ Amount
        ├─ Payment date
        ├─ Payment method
        └─ Receipt number
        ↓
DEPOSIT STATUS = PAID (Awaiting verification)
        ↓
MANAGER VERIFIES DEPOSIT
        ├─ Check amount matches requirement
        ├─ Check payment method valid
        └─ Approve verification
        ↓
DEPOSIT STATUS = VERIFIED
        ↓
LOAN CAN NOW BE DISBURSED
```

### Vault Transaction Flow

```
CASH MOVEMENT OCCURS
        ↓
TRANSACTION TYPE:
├─ Deposit to vault
├─ Withdrawal from vault
├─ Branch transfer
├─ Loan disbursement
└─ Payment collection
        ↓
RECORD TRANSACTION:
├─ Type
├─ Amount
├─ Source branch
├─ Destination branch
├─ Date/time
└─ Reference number
        ↓
SYSTEM UPDATES BRANCH BALANCES:
├─ Source branch: Balance - Amount
└─ Destination branch: Balance + Amount
        ↓
TRANSACTION RECORDED IN HISTORY
        ↓
AVAILABLE FOR REPORTING
```

---

## Role-Based Access Control

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION LAYER                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Login → Verify Credentials → Assign Role             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  AUTHORIZATION LAYER                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    ADMIN     │  │   MANAGER    │  │ LOAN OFFICER │     │
│  │              │  │              │  │              │     │
│  │ Permissions: │  │ Permissions: │  │ Permissions: │     │
│  │ • All views  │  │ • Portfolio  │  │ • Own groups │     │
│  │ • All actions│  │ • Expenses   │  │ • Own loans  │     │
│  │ • User mgmt  │  │ • Vault      │  │ • Approve*   │     │
│  │ • Reports    │  │ • Reports    │  │ • Disburse*  │     │
│  │ • Verify dep │  │ • Verify dep │  │ • Record dep │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  * Only if ≥15 groups (approve) and deposit verified       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   RESOURCE ACCESS LAYER                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Admin: Can access all resources                           │
│  Manager: Can access all loans, expenses, transactions     │
│  Officer: Can access only own groups and loans             │
│  Borrower: Can access only own loans                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema Overview

```
USERS & ROLES
├── accounts_user
│   ├── id (PK)
│   ├── username
│   ├── email
│   ├── role (admin, manager, officer, borrower)
│   ├── full_name
│   ├── phone_number
│   └── is_active
│
└── auth_permission
    ├── can_create_group
    ├── can_approve_loans
    ├── can_disburse_loans
    ├── can_verify_deposits
    └── can_manage_expenses

GROUPS & BORROWERS
├── clients_borrowergroup
│   ├── id (PK)
│   ├── name (unique)
│   ├── description
│   ├── branch (NEW)
│   ├── payment_day (NEW)
│   ├── assigned_officer (FK → User)
│   ├── max_members
│   ├── is_active
│   └── created_at
│
├── clients_borrower
│   ├── id (PK)
│   ├── full_name
│   ├── phone_number
│   ├── email
│   ├── group (FK → BorrowerGroup)
│   └── is_active
│
└── clients_officerassignment
    ├── id (PK)
    ├── officer (FK → User)
    ├── max_groups
    └── created_at

LOANS & PAYMENTS
├── loans_loantype
│   ├── id (PK)
│   ├── name
│   ├── interest_rate
│   ├── repayment_frequency (daily/weekly)
│   ├── min_term_days/weeks
│   ├── max_term_days/weeks
│   └── is_active
│
├── loans_loan
│   ├── id (PK)
│   ├── application_number (unique)
│   ├── borrower (FK → User)
│   ├── loan_officer (FK → User)
│   ├── loan_type (FK → LoanType)
│   ├── principal_amount
│   ├── interest_rate
│   ├── repayment_frequency
│   ├── term_days/weeks
│   ├── payment_amount
│   ├── total_amount
│   ├── amount_paid
│   ├── balance_remaining
│   ├── upfront_payment_required (10% of principal)
│   ├── upfront_payment_paid
│   ├── upfront_payment_verified
│   ├── status (pending/approved/disbursed/active/completed/defaulted)
│   ├── approval_date
│   ├── disbursement_date
│   ├── maturity_date
│   └── created_at
│
├── loans_securitydeposit (NEW)
│   ├── id (PK)
│   ├── loan (OneToOne → Loan)
│   ├── required_amount (10% of principal)
│   ├── paid_amount
│   ├── payment_date
│   ├── payment_method
│   ├── is_verified
│   ├── verified_by (FK → User)
│   ├── verification_date
│   ├── receipt_number
│   └── notes
│
├── payments_payment
│   ├── id (PK)
│   ├── loan (FK → Loan)
│   ├── amount
│   ├── payment_date
│   ├── payment_method
│   ├── recorded_by (FK → User)
│   └── created_at
│
└── payments_paymentschedule
    ├── id (PK)
    ├── loan (FK → Loan)
    ├── due_date
    ├── amount_due
    ├── is_paid
    └── paid_date

EXPENSES & VAULT
├── expenses_expensecategory
│   ├── id (PK)
│   ├── name
│   ├── description
│   └── is_active
│
├── expenses_expense
│   ├── id (PK)
│   ├── category (FK → ExpenseCategory)
│   ├── title
│   ├── description
│   ├── amount
│   ├── branch
│   ├── expense_date
│   ├── recorded_by (FK → User)
│   ├── is_approved
│   ├── approved_by (FK → User)
│   ├── receipt (FileField)
│   └── created_at
│
└── expenses_vaulttransaction
    ├── id (PK)
    ├── transaction_type (deposit/withdrawal/transfer/etc)
    ├── amount
    ├── branch
    ├── description
    ├── reference_number
    ├── recorded_by (FK → User)
    ├── transaction_date
    └── created_at
```

---

## Key Business Rules Engine

```
┌─────────────────────────────────────────────────────────────┐
│              BUSINESS RULES VALIDATION ENGINE               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ RULE 1: Loan Officer Approval Eligibility                 │
│ ├─ Check: Officer has ≥15 active groups?                  │
│ ├─ If NO: Block approval, show error message              │
│ └─ If YES: Allow approval                                 │
│                                                             │
│ RULE 2: Security Deposit Requirement                       │
│ ├─ When: Loan approved                                    │
│ ├─ Calculate: 10% of principal amount                     │
│ ├─ Create: SecurityDeposit record                         │
│ └─ Status: Required (awaiting payment)                    │
│                                                             │
│ RULE 3: Deposit Verification Before Disbursement          │
│ ├─ Check: Deposit verified?                               │
│ ├─ If NO: Block disbursement, show error                  │
│ └─ If YES: Allow disbursement                             │
│                                                             │
│ RULE 4: Loan Balance Calculation                          │
│ ├─ Formula: Total Amount - Amount Paid                    │
│ ├─ Exclude: Security deposit from balance                 │
│ └─ Update: After each payment                             │
│                                                             │
│ RULE 5: Expense Approval Workflow                         │
│ ├─ Status: Pending → Approved/Rejected                    │
│ ├─ Only: Manager/Admin can approve                        │
│ └─ Include: In financial reports only if approved         │
│                                                             │
│ RULE 6: Branch Balance Calculation                        │
│ ├─ Formula: Inflows - Outflows                            │
│ ├─ Inflows: Deposits, payments, transfers in              │
│ ├─ Outflows: Withdrawals, disbursements, transfers out    │
│ └─ Update: After each transaction                         │
│                                                             │
│ RULE 7: Officer Data Access                               │
│ ├─ Officer sees: Only own groups                          │
│ ├─ Officer sees: Only own borrowers                       │
│ ├─ Officer sees: Only own loans                           │
│ └─ Officer sees: Only own performance metrics             │
│                                                             │
│ RULE 8: Loan Status Transitions                           │
│ ├─ Pending → Approved (by officer/manager/admin)          │
│ ├─ Approved → Disbursed (by officer/manager/admin)        │
│ ├─ Disbursed → Active (automatic)                         │
│ ├─ Active → Completed (when fully paid)                   │
│ └─ Active → Defaulted (when overdue)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL INTEGRATIONS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ EMAIL SYSTEM                                               │
│ ├─ Loan application submitted                             │
│ ├─ Loan approved/rejected                                 │
│ ├─ Loan disbursed                                         │
│ ├─ Payment received                                       │
│ ├─ Overdue payment reminder                               │
│ └─ Deposit verification pending                           │
│                                                             │
│ SMS NOTIFICATIONS (Optional)                               │
│ ├─ Loan status updates                                    │
│ ├─ Payment reminders                                      │
│ └─ Overdue alerts                                         │
│                                                             │
│ REPORTING EXPORTS                                          │
│ ├─ PDF generation                                         │
│ ├─ CSV export                                             │
│ └─ Excel export                                           │
│                                                             │
│ AUDIT LOGGING                                              │
│ ├─ User actions tracked                                   │
│ ├─ Data changes logged                                    │
│ └─ Compliance reporting                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Performance Optimization

```
┌─────────────────────────────────────────────────────────────┐
│              PERFORMANCE OPTIMIZATION STRATEGIES            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ DATABASE OPTIMIZATION                                      │
│ ├─ Indexes on frequently queried fields                   │
│ ├─ Foreign key relationships optimized                    │
│ ├─ Query optimization for reports                         │
│ └─ Connection pooling                                     │
│                                                             │
│ CACHING STRATEGY                                           │
│ ├─ Cache dashboard data (5 min TTL)                       │
│ ├─ Cache report data (1 hour TTL)                         │
│ ├─ Cache user permissions                                 │
│ └─ Cache branch balances                                  │
│                                                             │
│ PAGINATION                                                 │
│ ├─ Loan lists: 20 items per page                          │
│ ├─ Transaction lists: 50 items per page                   │
│ ├─ Report data: 100 items per page                        │
│ └─ Lazy loading for large datasets                        │
│                                                             │
│ QUERY OPTIMIZATION                                         │
│ ├─ select_related() for foreign keys                      │
│ ├─ prefetch_related() for reverse relations               │
│ ├─ Aggregation queries for reports                        │
│ └─ Database-level calculations                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ AUTHENTICATION                                             │
│ ├─ Username/password login                                │
│ ├─ Session management                                     │
│ ├─ CSRF protection                                        │
│ └─ Secure password hashing                                │
│                                                             │
│ AUTHORIZATION                                              │
│ ├─ Role-based access control                              │
│ ├─ Permission decorators                                  │
│ ├─ Row-level permissions                                  │
│ └─ Object-level access checks                             │
│                                                             │
│ DATA PROTECTION                                            │
│ ├─ Input validation                                       │
│ ├─ SQL injection prevention (ORM)                         │
│ ├─ XSS protection                                         │
│ └─ HTTPS enforcement                                      │
│                                                             │
│ AUDIT & COMPLIANCE                                         │
│ ├─ User action logging                                    │
│ ├─ Data change tracking                                   │
│ ├─ Compliance reporting                                   │
│ └─ Immutable audit logs                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  DEPLOYMENT ENVIRONMENT                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ DEVELOPMENT                                                │
│ ├─ Local machine                                          │
│ ├─ SQLite or local MySQL                                  │
│ ├─ Debug mode enabled                                     │
│ └─ Hot reload enabled                                     │
│                                                             │
│ STAGING                                                    │
│ ├─ Test server                                            │
│ ├─ MySQL database                                         │
│ ├─ Debug mode disabled                                    │
│ └─ Full testing suite                                     │
│                                                             │
│ PRODUCTION                                                 │
│ ├─ Cloud server (AWS/Azure/GCP)                           │
│ ├─ MySQL database (managed)                               │
│ ├─ HTTPS enabled                                          │
│ ├─ Backup & recovery                                      │
│ ├─ Monitoring & alerts                                    │
│ └─ Load balancing                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

**PalmCash System Architecture v1.0** | December 2025
