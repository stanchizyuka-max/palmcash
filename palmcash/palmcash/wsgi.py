"""
WSGI config for palmcash project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "palmcash.settings")

# Run migrations on startup
try:
    call_command('migrate', verbosity=0, interactive=False)
except Exception as e:
    print(f"Migration error: {e}", file=sys.stderr)

application = get_wsgi_application()
