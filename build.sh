#!/usr/bin/env bash
# exit on error
set -o errexit

# Ensure pg_config is in PATH
export PATH="/usr/lib/postgresql/15/bin:$PATH"

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate 