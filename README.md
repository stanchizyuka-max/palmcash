# Palm Cash - Comprehensive Loan Management System

Palm Cash is a modern, web-based loan management system built with Django that streamlines the entire loan lifecycle from application to repayment. Designed for the Zambian market with ZMW (Kwacha) currency support.

 🎯 Objectives

- **Streamline and digitize** the full loan management lifecycle
- **Centralize borrower and transaction records** for easy access
- **Support multi-level role-based system access** (Admin, Loan Officer, Borrower)
- **Generate automated reports** for financial tracking and compliance
- **Provide timely alerts and notifications** to borrowers and staff

 ✨ Key Features

Client Registration & Management
- User registration with role-based access (Admin, Loan Officer, Borrower)
- Comprehensive client profiles with personal, employment, and financial information
- Document verification and KYC compliance

Loan Application Management
- Online loan application submission
- Multi-stage approval workflow (Submission → Review → Approval/Rejection → Disbursement)
- Support for multiple loan types with configurable terms and rates
- Automated loan calculations (EMI, interest, total amount)

Loan Disbursement & Tracking
- Loan disbursement management
- Real-time loan status tracking
- Payment schedule generation
- Balance and payment history tracking

Repayment Management
- Automated payment schedule creation
- Multiple payment methods support (Cash, Bank Transfer, Check, Mobile Money, Card)
- Interest and penalty calculations
- Overdue payment tracking and management

Automated Notifications
- SMS and Email notifications for:
  - Loan approvals/rejections
  - Payment due reminders
  - Overdue payment alerts
  - Disbursement confirmations
- Customizable notification templates

Document Management
- Secure document upload system
- Document type management (ID, Income Proof, Bank Statements, etc.)
- Document verification workflow
- File size and format validation

Financial Dashboard & Analytics
- Role-based dashboards
- Real-time financial metrics
- Loan portfolio overview
- Payment performance analytics
- Monthly disbursement reports

Security & Compliance
- Role-based access control
- Audit logs for all transactions
- Secure file uploads
- Data encryption and protection

## 🏗️ System Architecture

### Apps Structure
- **accounts**: User management and authentication
- **loans**: Loan application and management
- **clients**: Client profile management
- **payments**: Payment processing and tracking
- **documents**: Document upload and verification
- **notifications**: Alert and notification system
- **reports**: Financial reporting and analytics
- **dashboard**: Main dashboard and overview

### User Roles
1. **Admin**: Full system access, user management, system configuration
2. **Loan Officer**: Loan review, approval, client management, reports
3. **Borrower**: Loan application, payment tracking, document upload

## 🚀 Getting Started

### Quick Links
- **New to the project?** → Read [SETUP_NEW_LAPTOP.md](setup/SETUP_NEW_LAPTOP.md) for complete setup instructions
- **Deploy to PythonAnywhere?** → Read [DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md)
- **System architecture?** → Check [SYSTEM_ARCHITECTURE_OVERVIEW.md](SYSTEM_ARCHITECTURE_OVERVIEW.md)
- **Notifications setup?** → See [COMMUNICATION_SYSTEM.md](COMMUNICATION_SYSTEM.md)

### Prerequisites
- Python 3.11+
- Django 4.2.7
- MariaDB 10.5+ (or MySQL 8.0+)
- Redis (for Celery background tasks)
- Git

### Quick Start for New Developers (Fresh Laptop)

If you're setting up Palm Cash on a new laptop with nothing installed, follow these steps:

#### Step 1: Install Required Software

**Windows:**
1. **Python 3.11+**
   - Download from https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Verify: `python --version`

2. **Git**
   - Download from https://git-scm.com/download/win
   - Use default installation settings
   - Verify: `git --version`

3. **MariaDB 10.6+**
   - Download from https://mariadb.org/download/
   - Choose Windows MSI installer
   - During installation:
     - Set port to 3306 (or 3307 if 3306 is in use)
     - Set root password (remember this!)
     - Install as service
   - Verify: `mysql -u root -p -e "SELECT VERSION();"`

4. **Redis** (optional, for background tasks)
   - Download from https://github.com/microsoftarchive/redis/releases
   - Or use Windows Subsystem for Linux (WSL)

**macOS:**
```bash
# Install Homebrew first if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install Git
brew install git

# Install MariaDB
brew install mariadb

# Install Redis
brew install redis

# Start MariaDB
brew services start mariadb

# Start Redis
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
# Update package manager
sudo apt update

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip

# Install Git
sudo apt install git

# Install MariaDB
sudo apt install mariadb-server

# Install Redis
sudo apt install redis-server

# Start services
sudo systemctl start mariadb
sudo systemctl start redis-server
```

#### Step 2: Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd palmcash

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Step 3: Configure Database

```bash
# Create database
mysql -u root -p -e "CREATE DATABASE palmcash_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Create .env file
cp .env.example .env

# Edit .env with your database credentials
# DB_USER=root
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=3306 (or 3307)
```

#### Step 4: Initialize Application

```bash
# Run migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser

# Load initial data (optional)
python manage.py populate_initial_data

# Collect static files
python manage.py collectstatic --noinput
```

#### Step 5: Run Development Server

```bash
# Start Django development server
python manage.py runserver

# In another terminal, start Celery (for background tasks)
celery -A palmcash worker -l info

# In another terminal, start Redis (if using background tasks)
redis-server
```

Access the application:
- Main site: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/
- Dashboard: http://127.0.0.1:8000/dashboard/

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd palmcash
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Populate initial data** (optional)
   ```bash
   python manage.py populate_initial_data
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/
   - Dashboard: http://127.0.0.1:8000/dashboard/

### Database Configuration

Palm Cash uses MariaDB 10.6+ for production. Update your `.env` file:

```env
DB_NAME=palmcash_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3307
```

### Default Users (after running populate_initial_data)
- **Admin**: username: `admin`, password: `admin123`
- **Loan Officer**: username: `loan_officer`, password: `password123`
- **Borrower**: username: `borrower1`, password: `password123`

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_loans.py

# Run with verbose output
pytest -v
```

### Property-Based Testing

Palm Cash uses Hypothesis for property-based testing to ensure correctness properties hold across all inputs:

```bash
# Run property-based tests
pytest --hypothesis-seed=0
```

## 📊 Development Workflow

### Database Troubleshooting

If you encounter database connection issues:

1. **Verify MariaDB is running**
   ```bash
   mysql -h localhost -P 3307 -u root -e "SELECT VERSION();"
   ```

2. **Check database exists**
   ```bash
   mysql -h localhost -P 3307 -u root -e "SHOW DATABASES LIKE 'palmcash%';"
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

### Environment Setup

Create a `.env` file in the project root with:

```env
# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Database Configuration
DB_NAME=palmcash_db
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3307

# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key
```

## 📋 Project Structure

```
palmcash/
├── accounts/          # User authentication and management
├── loans/             # Loan application and management
├── clients/           # Client profile management
├── payments/          # Payment processing
├── documents/         # Document management
├── notifications/     # Alert and notification system
├── reports/           # Financial reporting
├── dashboard/         # Main dashboard
├── adminpanel/        # Admin interface
├── expenses/          # Expense tracking
├── templates/         # HTML templates
├── static/            # CSS, JavaScript, images
├── manage.py          # Django management script
└── requirements.txt   # Python dependencies
```

### For Borrowers
1. Register for an account
2. Complete your profile with personal and financial information
3. Upload required documents (ID, income proof, etc.)
4. Apply for a loan by selecting loan type and amount
5. Track application status and receive notifications
6. Make payments according to the payment schedule

### For Loan Officers
1. Review loan applications
2. Verify borrower documents
3. Approve or reject loan applications
4. Manage loan disbursements
5. Track payments and handle overdue accounts
6. Generate reports for management

### For Administrators
1. Manage system users and roles
2. Configure loan types and interest rates
3. Set up notification templates
4. Monitor system performance
5. Generate comprehensive reports
6. Manage system settings

## 🔧 Configuration

### Loan Types
Configure different loan products in the admin panel (amounts in ZMW):
- Personal Loans (K2,000 - K250,000)
- Business Loans (K25,000 - K1,000,000)
- Auto Loans (K25,000 - K500,000)
- Home Improvement Loans (K10,000 - K375,000)
- Agricultural Loans (K15,000 - K750,000)

### Notification Settings
Set up email and SMS notifications:
- SMTP configuration for emails
- SMS gateway integration
- Notification templates customization

Document Types
Configure required document types:
- National ID
- Proof of Income
- Bank Statements
- Employment Letters
- Collateral Documents

Reports Available

1. **Loan Portfolio Report**: Overview of all loans by status
2. **Payment Performance Report**: Collection rates and overdue analysis
3. **Financial Summary Report**: Revenue, disbursements, and profitability
4. **Client Analysis Report**: Borrower demographics and behavior
5. **Compliance Report**: Regulatory compliance tracking

Security Features

- User authentication and authorization
- Role-based access control
- Secure file uploads with validation
- CSRF protection
- SQL injection prevention
- XSS protection
- Audit trail for all operations

Future Enhancements

- Mobile application
- Advanced analytics and AI-powered risk assessment
- Integration with external credit bureaus
- Automated loan approval workflows
- Multi-currency support
- Advanced reporting with data visualization
- API for third-party integrations

📞 Support

For technical support or questions about Palm Cash, please contact the development team or refer to the documentation.
