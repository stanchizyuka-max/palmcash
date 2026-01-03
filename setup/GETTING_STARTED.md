# Getting Started with Palm Cash

Welcome to Palm Cash! This guide will help you get up and running quickly.

## For New Developers (Fresh Laptop)

If you're setting up Palm Cash on a new laptop with nothing installed:

1. **Read**: [SETUP_NEW_LAPTOP.md](SETUP_NEW_LAPTOP.md) - Complete step-by-step setup guide
2. **Follow**: All steps in that guide (takes 30-45 minutes)
3. **Verify**: Use [DEVELOPER_CHECKLIST.md](DEVELOPER_CHECKLIST.md) to confirm everything works

## For Existing Developers

If you already have the project set up:

1. **Activate virtual environment**:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Update dependencies** (if needed):
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations** (if database schema changed):
   ```bash
   python manage.py migrate
   ```

4. **Start development server**:
   ```bash
   python manage.py runserver
   ```

5. **Access the application**:
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/
   - Dashboard: http://127.0.0.1:8000/dashboard/

## Project Documentation

- **[README.md](README.md)** - Project overview and features
- **[SETUP_NEW_LAPTOP.md](SETUP_NEW_LAPTOP.md)** - Complete setup guide for new developers
- **[DEVELOPER_CHECKLIST.md](DEVELOPER_CHECKLIST.md)** - Verification checklist
- **[SYSTEM_ARCHITECTURE_OVERVIEW.md](SYSTEM_ARCHITECTURE_OVERVIEW.md)** - System design and architecture
- **[COMMUNICATION_SYSTEM.md](COMMUNICATION_SYSTEM.md)** - Notification and messaging setup
- **[INTERNAL_COMMUNICATION_GUIDE.md](INTERNAL_COMMUNICATION_GUIDE.md)** - Internal messaging system

## Quick Reference

### Common Commands

```bash
# Run development server
python manage.py runserver

# Run tests
pytest

# Run tests with coverage
pytest --cov=.

# Create database migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Start Celery worker (background tasks)
celery -A palmcash worker -l info
```

### Database Commands

```bash
# Connect to database
mysql -u root -p

# Show databases
SHOW DATABASES;

# Use palmcash database
USE palmcash_db;

# Show tables
SHOW TABLES;

# Exit
EXIT;
```

### Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Deactivate
deactivate
```

## Troubleshooting

### "Database connection refused"
1. Check MariaDB is running
2. Verify credentials in `.env`
3. Ensure database exists: `mysql -u root -p -e "SHOW DATABASES;"`

### "Module not found"
1. Activate virtual environment
2. Run `pip install -r requirements.txt`

### "Port 3306 already in use"
1. Use port 3307 in `.env`
2. Or stop the service using port 3306

### "Static files not found"
1. Run `python manage.py collectstatic --noinput`

For more troubleshooting, see [SETUP_NEW_LAPTOP.md](SETUP_NEW_LAPTOP.md#troubleshooting)

## Project Structure

```
palmcash/
├── accounts/          # User authentication
├── loans/             # Loan management
├── clients/           # Client profiles
├── payments/          # Payment processing
├── documents/         # Document management
├── notifications/     # Alerts and notifications
├── reports/           # Financial reporting
├── dashboard/         # Main dashboard
├── adminpanel/        # Admin interface
├── expenses/          # Expense tracking
├── templates/         # HTML templates
├── static/            # CSS, JavaScript, images
├── manage.py          # Django management
└── requirements.txt   # Python dependencies
```

## Next Steps

1. **Read the documentation** - Start with [README.md](README.md)
2. **Understand the architecture** - Check [SYSTEM_ARCHITECTURE_OVERVIEW.md](SYSTEM_ARCHITECTURE_OVERVIEW.md)
3. **Set up your IDE** - Configure your editor for Python development
4. **Run the tests** - Verify everything works: `pytest`
5. **Start developing** - Pick a feature and start coding!

## Getting Help

- Check the troubleshooting section above
- Review the relevant documentation file
- Check error messages carefully
- Contact the development team

## Development Workflow

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `pytest`
4. Commit your changes: `git commit -m "Your message"`
5. Push to repository: `git push origin feature/your-feature`
6. Create a pull request

## Code Quality

- Run tests before committing: `pytest`
- Check coverage: `pytest --cov=.`
- Follow PEP 8 style guide
- Write meaningful commit messages
- Add docstrings to functions and classes

Happy coding! 🚀

---

**Questions?** Check the documentation or contact the development team.
