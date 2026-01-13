#!/bin/bash
# Run migrations on PythonAnywhere

cd /home/stan13/palmcash
source /home/stan13/.virtualenvs/palmcash-env/bin/activate
python manage.py migrate
