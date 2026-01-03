# Developer Setup Checklist

Use this checklist to ensure you have everything set up correctly before starting development.

## Pre-Setup
- [ ] You have administrator access on your laptop
- [ ] You have at least 2GB free disk space
- [ ] You have internet connection
- [ ] You have 30-45 minutes available

## System Dependencies
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Git installed (`git --version`)
- [ ] MariaDB 10.5+ or MySQL 8.0+ installed (`mysql --version`)
- [ ] Redis installed (optional but recommended) (`redis-cli ping`)

## Repository Setup
- [ ] Repository cloned to your machine
- [ ] You're in the `palmcash` directory
- [ ] Virtual environment created (`python -m venv venv`)
- [ ] Virtual environment activated (you see `(venv)` in terminal)

## Python Dependencies
- [ ] `pip install -r requirements.txt` completed successfully
- [ ] No error messages during installation
- [ ] All packages installed: `pip list | grep -i django`

## Database Setup
- [ ] MariaDB/MySQL service is running
- [ ] Database `palmcash_db` created
- [ ] `.env` file created from `.env.example`
- [ ] Database credentials in `.env` are correct
- [ ] Can connect to database: `mysql -u root -p -e "SHOW DATABASES;"`

## Application Initialization
- [ ] Migrations run successfully: `python manage.py migrate`
- [ ] Superuser created: `python manage.py createsuperuser`
- [ ] Static files collected: `python manage.py collectstatic --noinput`
- [ ] Initial data loaded (optional): `python manage.py populate_initial_data`

## Development Server
- [ ] Django server starts: `python manage.py runserver`
- [ ] Can access http://127.0.0.1:8000/
- [ ] Can access admin panel: http://127.0.0.1:8000/admin/
- [ ] Can login with superuser credentials

## Optional - Background Tasks
- [ ] Redis running (if using background tasks)
- [ ] Celery worker starts: `celery -A palmcash worker -l info`
- [ ] No connection errors in Celery output

## Code Quality
- [ ] Can run tests: `pytest`
- [ ] Can run tests with coverage: `pytest --cov=.`
- [ ] No import errors in main modules

## IDE/Editor Setup
- [ ] IDE/Editor installed (VS Code, PyCharm, etc.)
- [ ] Python extension/plugin installed
- [ ] Virtual environment selected as Python interpreter
- [ ] Linting configured (optional but recommended)

## Git Setup
- [ ] Git configured: `git config --global user.name "Your Name"`
- [ ] Git configured: `git config --global user.email "your@email.com"`
- [ ] Can pull latest changes: `git pull`
- [ ] Can create branches: `git checkout -b feature/your-feature`

## Documentation
- [ ] Read [README.md](README.md)
- [ ] Read [SETUP_NEW_LAPTOP.md](SETUP_NEW_LAPTOP.md)
- [ ] Read [SYSTEM_ARCHITECTURE_OVERVIEW.md](SYSTEM_ARCHITECTURE_OVERVIEW.md)
- [ ] Familiar with project structure

## Ready to Develop!
- [ ] All items above are checked
- [ ] You understand the project structure
- [ ] You know how to run tests
- [ ] You know how to start the development server
- [ ] You're ready to start coding!

## Troubleshooting

If any item above fails:

1. **Python/Git not found**: Restart terminal after installation, or add to PATH
2. **Database connection failed**: Check MariaDB is running, verify credentials in `.env`
3. **Port 3306 in use**: Use port 3307 in `.env` instead
4. **Module not found**: Activate virtual environment, run `pip install -r requirements.txt`
5. **Static files not found**: Run `python manage.py collectstatic --noinput`
6. **Migration errors**: Check database connection, try `python manage.py migrate --fake-initial`

See [SETUP_NEW_LAPTOP.md](SETUP_NEW_LAPTOP.md) for detailed troubleshooting.

## Quick Commands Reference

```bash
# Activate virtual environment
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

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

# Start Celery worker
celery -A palmcash worker -l info

# Deactivate virtual environment
deactivate
```

## Getting Help

1. Check the troubleshooting section above
2. Review error messages carefully
3. Check [SETUP_NEW_LAPTOP.md](SETUP_NEW_LAPTOP.md)
4. Contact the development team

Good luck! 🚀
