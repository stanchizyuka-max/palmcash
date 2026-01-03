# Palm Cash - Setup Guide for New Laptop

Complete step-by-step guide to get Palm Cash running on a fresh laptop.

## Prerequisites Checklist

Before starting, ensure you have:
- [ ] Internet connection
- [ ] Administrator access on your laptop
- [ ] At least 2GB free disk space
- [ ] 30-45 minutes for complete setup

## Step 1: Install System Dependencies

### Windows

#### 1.1 Install Python 3.11+
1. Go to https://www.python.org/downloads/
2. Download Python 3.11 or later
3. Run the installer
4. **IMPORTANT**: Check "Add Python to PATH"
5. Click "Install Now"
6. Verify installation:
   ```cmd
   python --version
   ```

#### 1.2 Install Git
1. Go to https://git-scm.com/download/win
2. Download Git for Windows
3. Run installer with default settings
4. Verify installation:
   ```cmd
   git --version
   ```

#### 1.3 Install MariaDB 10.6+
1. Go to https://mariadb.org/download/
2. Download MariaDB 10.6 MSI for Windows
3. Run installer
4. During setup:
   - Port: 3306 (or 3307 if 3306 is busy)
   - Root password: **Set a strong password and remember it**
   - Install as Windows service: YES
5. Verify installation:
   ```cmd
   mysql -u root -p -e "SELECT VERSION();"
   ```
   (Enter your root password when prompted)

#### 1.4 Install Redis (Optional - for background tasks)
1. Go to https://github.com/microsoftarchive/redis/releases
2. Download `Redis-x64-*.msi`
3. Run installer with default settings
4. Verify:
   ```cmd
   redis-cli ping
   ```

### macOS

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install Git
brew install git

# Install MariaDB
brew install mariadb

# Install Redis (optional)
brew install redis

# Start MariaDB
brew services start mariadb

# Start Redis (optional)
brew services start redis

# Verify installations
python3 --version
git --version
mysql --version
```

### Linux (Ubuntu/Debian)

```bash
# Update package manager
sudo apt update

# Install Python and pip
sudo apt install python3.11 python3.11-venv python3-pip

# Install Git
sudo apt install git

# Install MariaDB
sudo apt install mariadb-server

# Install Redis (optional)
sudo apt install redis-server

# Start services
sudo systemctl start mariadb
sudo systemctl start redis-server

# Enable services to start on boot
sudo systemctl enable mariadb
sudo systemctl enable redis-server

# Verify installations
python3 --version
git --version
mysql --version
```

## Step 2: Clone Repository

```bash
# Navigate to where you want to store the project
cd ~/Documents  # or your preferred location

# Clone the repository
git clone <repository-url>
cd palmcash
```

## Step 3: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Configure Database

### 4.1 Create Database

```bash
# Connect to MariaDB
mysql -u root -p

# In the MySQL prompt, run:
CREATE DATABASE palmcash_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 4.2 Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# On Windows: notepad .env
# On macOS/Linux: nano .env
```

Edit `.env` and set:
```env
# Database Configuration
DB_NAME=palmcash_db
DB_USER=root
DB_PASSWORD=your_root_password_here
DB_HOST=localhost
DB_PORT=3306  # or 3307 if you used that port

# Email Configuration (optional for development)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Django Settings
DEBUG=True
SECRET_KEY=django-insecure-your-secret-key-here
```

## Step 5: Initialize Application

```bash
# Make sure virtual environment is activated
# (you should see (venv) in your terminal prompt)

# Run database migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
# Follow prompts to create admin account

# Load initial data (optional)
python manage.py populate_initial_data

# Collect static files
python manage.py collectstatic --noinput
```

## Step 6: Run Application

### Terminal 1: Django Development Server
```bash
# Make sure you're in the palmcash directory with venv activated
python manage.py runserver
```

### Terminal 2: Celery Worker (optional - for background tasks)
```bash
# In a new terminal, activate venv first
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

celery -A palmcash worker -l info
```

### Terminal 3: Redis Server (optional - if using background tasks)
```bash
# Windows: redis-server
# macOS/Linux: redis-server
```

## Step 7: Access Application

Open your browser and go to:

- **Main Site**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **Dashboard**: http://127.0.0.1:8000/dashboard/

Login with the superuser account you created in Step 5.

## Troubleshooting

### "Python not found"
- Make sure Python is added to PATH
- Restart your terminal after installing Python
- Try `python3` instead of `python`

### "Database connection refused"
- Verify MariaDB is running:
  - Windows: Check Services (services.msc)
  - macOS: `brew services list`
  - Linux: `sudo systemctl status mariadb`
- Check database credentials in `.env`
- Verify database exists: `mysql -u root -p -e "SHOW DATABASES;"`

### "Port 3306 already in use"
- Use port 3307 instead in `.env`
- Or stop the service using port 3306

### "Module not found" errors
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Try `pip install --upgrade pip setuptools wheel`

### "Static files not found"
- Run `python manage.py collectstatic --noinput`
- Check that `STATIC_ROOT` directory exists

## Next Steps

1. Read the main [README.md](README.md) for feature overview
2. Check [SYSTEM_ARCHITECTURE_OVERVIEW.md](SYSTEM_ARCHITECTURE_OVERVIEW.md) for system design
3. Review [COMMUNICATION_SYSTEM.md](COMMUNICATION_SYSTEM.md) for notification setup
4. Start developing!

## Getting Help

If you encounter issues:
1. Check the Troubleshooting section above
2. Review error messages carefully
3. Check that all prerequisites are installed
4. Verify database connection
5. Contact the development team

## Quick Reference Commands

```bash
# Activate virtual environment
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
pytest

# Run tests with coverage
pytest --cov=.

# Deactivate virtual environment
deactivate
```

Happy coding! 🚀
