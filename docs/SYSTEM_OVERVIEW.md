# Palm Cash Loan Management System - System Overview

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [System Purpose](#system-purpose)
3. [Key Features](#key-features)
4. [User Roles](#user-roles)
5. [System Architecture](#system-architecture)
6. [Technology Stack](#technology-stack)
7. [Core Modules](#core-modules)
8. [Business Workflows](#business-workflows)
9. [Security Features](#security-features)
10. [Integration Points](#integration-points)

---

## 1. Introduction

Palm Cash is a comprehensive loan management system designed for microfinance institutions in Zambia. The system streamlines loan origination, disbursement, repayment tracking, and reporting processes.

### System Information
- **Name**: Palm Cash Loan Management System
- **Version**: 1.0
- **Platform**: Web-based (Django)
- **Currency**: Zambian Kwacha (ZMW)
- **Language**: English
- **Deployment**: Cloud-based

---

## 2. System Purpose

### Primary Objectives
1. **Digitize Loan Operations** - Move from manual to automated loan processing
2. **Improve Efficiency** - Reduce processing time and errors
3. **Enhance Tracking** - Real-time monitoring of loans and payments
4. **Ensure Compliance** - Meet regulatory requirements
5. **Provide Insights** - Generate reports and analytics

### Target Users
- Microfinance institutions
- Community banks
- Lending cooperatives
- Financial service providers

---

## 3. Key Features

### Loan Management
- ✅ Loan application processing
- ✅ Multi-step approval workflow
- ✅ Automated interest calculation
- ✅ Flexible repayment schedules (daily/weekly)
- ✅ Loan disbursement tracking
- ✅ Backdating support for historical data

### Payment Processing
- ✅ Payment recording and verification
- ✅ Partial payment support
- ✅ Payment history tracking
- ✅ Automated balance calculation
- ✅ Receipt generation

### Vault Management
- ✅ Cash flow tracking
- ✅ Branch-wise vault management
- ✅ Transaction recording (inflows/outflows)
- ✅ Balance reconciliation
- ✅ Vault reports

### User Management
- ✅ Role-based access control
- ✅ User registration and approval
- ✅ Branch assignment
- ✅ Activity tracking
- ✅ Search and filter capabilities

### Reporting
- ✅ Loan portfolio reports
- ✅ Collection reports
- ✅ Vault reports
- ✅ Performance reports
- ✅ Custom date ranges

### Notifications
- ✅ In-app notifications
- ✅ Payment confirmations
- ✅ Loan status updates
- ✅ Branch-filtered notifications
- ✅ Real-time alerts

---

## 4. User Roles

### Administrator
**Responsibilities**:
- System configuration
- User management (all roles)
- Branch management
- System-wide reports
- Security settings

**Access Level**: Full system access

**Key Features**:
- View all branches
- Manage all users
- Configure system settings
- Access all reports
- Audit logs

### Manager
**Responsibilities**:
- Branch operations oversight
- Loan approval
- Officer supervision
- Branch reporting
- Client management

**Access Level**: Branch-level access

**Key Features**:
- Approve/reject loans
- View branch clients
- Manage branch officers
- Branch reports
- Payment verification

### Loan Officer
**Responsibilities**:
- Client registration
- Loan application
- Payment collection
- Client follow-up
- Daily reporting

**Access Level**: Assigned clients only

**Key Features**:
- Register borrowers
- Create loan applications
- Record payments
- View assigned clients
- Collection reports

### Borrower
**Responsibilities**:
- Loan application
- Payment tracking
- Document submission
- Profile management

**Access Level**: Own data only

**Key Features**:
- View loan status
- Payment history
- Loan balance
- Profile updates
- Notifications

---

## 5. System Architecture

### Architecture Type
**Monolithic Web Application** with modular Django apps

### Layers

#### 1. Presentation Layer
- **Technology**: HTML, CSS (Tailwind), JavaScript
- **Components**: Templates, Forms, UI Components
- **Responsibility**: User interface and interaction

#### 2. Application Layer
- **Technology**: Django Views, Forms
- **Components**: Business logic, Validation, Workflows
- **Responsibility**: Process user requests

#### 3. Data Layer
- **Technology**: Django ORM, PostgreSQL
- **Components**: Models, Database queries
- **Responsibility**: Data persistence

#### 4. Integration Layer
- **Technology**: Django REST Framework (future)
- **Components**: APIs, External integrations
- **Responsibility**: Third-party connections

### System Components

```
┌─────────────────────────────────────────────────┐
│           Web Browser (Client)                  │
└─────────────────┬───────────────────────────────┘
                  │ HTTPS
┌─────────────────▼───────────────────────────────┐
│              Nginx (Web Server)                 │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│          Gunicorn (WSGI Server)                 │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│         Django Application                      │
│  ┌──────────────────────────────────────────┐  │
│  │  Apps: accounts, loans, payments,        │  │
│  │        clients, vault, reports           │  │
│  └──────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│         PostgreSQL Database                     │
└─────────────────────────────────────────────────┘
```

---

## 6. Technology Stack

### Backend
- **Framework**: Django 4.2+
- **Language**: Python 3.11+
- **Database**: PostgreSQL 14+
- **ORM**: Django ORM
- **Authentication**: Django Auth

### Frontend
- **CSS Framework**: Tailwind CSS
- **JavaScript**: Vanilla JS
- **Icons**: Font Awesome
- **Charts**: Chart.js (for reports)

### Server
- **Web Server**: Nginx
- **Application Server**: Gunicorn
- **OS**: Ubuntu 20.04+ / Linux
- **Python Environment**: venv

### Development Tools
- **Version Control**: Git / GitHub
- **IDE**: VS Code, PyCharm
- **Testing**: Django Test Framework
- **Linting**: Flake8, Black

---

## 7. Core Modules

### 1. Accounts Module
**Purpose**: User management and authentication

**Key Models**:
- User (extended AbstractUser)
- LoginSession
- UserAuditLog

**Features**:
- User registration
- Login/logout
- Password reset
- Profile management
- Role assignment

### 2. Loans Module
**Purpose**: Loan lifecycle management

**Key Models**:
- Loan
- LoanApplication
- LoanSchedule
- LoanStatus

**Features**:
- Loan application
- Approval workflow
- Disbursement
- Interest calculation
- Status tracking

### 3. Payments Module
**Purpose**: Payment processing and tracking

**Key Models**:
- Payment
- PaymentVerification
- PaymentHistory

**Features**:
- Payment recording
- Verification workflow
- Balance calculation
- Payment history
- Receipt generation

### 4. Clients Module
**Purpose**: Borrower and group management

**Key Models**:
- BorrowerGroup
- GroupMembership
- OfficerAssignment

**Features**:
- Client registration
- Group management
- Officer assignment
- Client search
- Document management

### 5. Vault Module
**Purpose**: Cash flow and vault management

**Key Models**:
- WeeklyVault
- VaultTransaction
- VaultReconciliation

**Features**:
- Transaction recording
- Balance tracking
- Branch vaults
- Reconciliation
- Vault reports

### 6. Reports Module
**Purpose**: Reporting and analytics

**Key Models**:
- Report
- ReportSchedule

**Features**:
- Loan reports
- Collection reports
- Performance reports
- Custom reports
- Export to PDF/Excel

### 7. Notifications Module
**Purpose**: User notifications

**Key Models**:
- Notification
- NotificationTemplate

**Features**:
- In-app notifications
- Email notifications (future)
- SMS notifications (future)
- Notification preferences

---

## 8. Business Workflows

### Loan Application Workflow

```
1. Officer registers borrower
   ↓
2. Officer creates loan application
   ↓
3. Officer records processing fee
   ↓
4. Manager reviews application
   ↓
5. Manager approves/rejects
   ↓
6. If approved: Loan disbursement
   ↓
7. Loan becomes active
   ↓
8. Payments collected
   ↓
9. Loan completion
```

### Payment Processing Workflow

```
1. Officer collects payment from borrower
   ↓
2. Officer records payment in system
   ↓
3. Payment marked as "pending"
   ↓
4. Manager verifies payment
   ↓
5. Manager confirms/rejects
   ↓
6. If confirmed: Loan balance updated
   ↓
7. Vault transaction recorded
   ↓
8. Notification sent to officer
```

### User Registration Workflow

```
1. Admin/Manager creates user account
   ↓
2. User receives credentials
   ↓
3. User logs in
   ↓
4. User completes profile
   ↓
5. Admin/Manager assigns role
   ↓
6. User gains access based on role
```

---

## 9. Security Features

### Authentication
- ✅ Password hashing (Django's PBKDF2)
- ✅ Session management
- ✅ Login tracking
- ✅ Password reset via email
- ✅ Account lockout (future)

### Authorization
- ✅ Role-based access control (RBAC)
- ✅ Permission-based views
- ✅ Branch-level data isolation
- ✅ Object-level permissions

### Data Security
- ✅ HTTPS encryption
- ✅ SQL injection protection (ORM)
- ✅ XSS protection (Django templates)
- ✅ CSRF protection
- ✅ Secure password storage

### Audit Trail
- ✅ User activity logging
- ✅ Login/logout tracking
- ✅ Transaction history
- ✅ Change tracking
- ✅ Audit reports

---

## 10. Integration Points

### Current Integrations
- None (standalone system)

### Planned Integrations
- **Mobile Money**: MTN, Airtel, Zamtel
- **SMS Gateway**: Bulk SMS for notifications
- **Email Service**: SMTP for email notifications
- **Accounting Software**: QuickBooks, Xero
- **Credit Bureau**: Credit reference checks
- **Banking APIs**: Bank account verification

---

## 📊 System Statistics

### Performance Metrics
- **Users**: 101 (81 borrowers, 14 officers, 4 managers, 2 admins)
- **Branches**: Multiple (KUKU, Mandevu, etc.)
- **Loans**: Active loan portfolio
- **Payments**: Daily payment processing
- **Uptime**: 99.9% target

### Capacity
- **Concurrent Users**: 100+
- **Database Size**: Scalable
- **Transaction Volume**: 1000+ per day
- **Response Time**: < 2 seconds

---

## 🔄 System Updates

### Recent Updates (May 2026)
- ✅ Search and filter features
- ✅ Branch column in user management
- ✅ Phone validation for 055/057 prefixes
- ✅ Notification branch filtering
- ✅ Code cleanup and optimization

### Upcoming Features
- 📱 Mobile app
- 💬 SMS notifications
- 📧 Email notifications
- 📊 Advanced analytics
- 🔗 Mobile money integration

---

## 📞 Support and Maintenance

### Support Channels
- **Technical Support**: support@palmcash.com
- **Documentation**: docs.palmcash.com
- **GitHub Issues**: github.com/palmcash/issues

### Maintenance Schedule
- **Daily Backups**: 2:00 AM
- **Weekly Updates**: Sundays 1:00 AM
- **Monthly Maintenance**: First Sunday of month

---

**Document Version**: 1.0
**Last Updated**: May 19, 2026
**Author**: Palm Cash Development Team
