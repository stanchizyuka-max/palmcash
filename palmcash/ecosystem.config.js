module.exports = {
  "apps": [
    {
      "name": "palmcashloans.site",
      "script": "gunicorn",
      "args": "--bind=unix:/var/www/iwnd349/data/python/6.sock --workers=4 palmcash.wsgi:application",
      "cwd": "/var/www/iwnd349/data/www/palmcashloans.site/palmcash",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "DJANGO_SETTINGS_MODULE": "palmcash.settings"
      }
    }
  ]
}
