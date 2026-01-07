"""
WSGI config for palmcash project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "palmcash.settings")

# Get WSGI application first
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Run migrations on startup (after app is initialized)
try:
    from django.core.management import call_command
    call_command('migrate', verbosity=0, interactive=False)
except Exception as e:
    print(f"Migration error: {e}", file=sys.stderr)
    # Don't fail the app startup if migrations fail
