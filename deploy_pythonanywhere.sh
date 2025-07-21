#!/bin/bash

echo "Starting deployment process..."

# Create and activate virtual environment
echo "Setting up virtual environment..."
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create PostgreSQL database if it doesn't exist
echo "Setting up database..."
if ! psql -lqt | cut -d \| -f 1 | grep -qw 'aniket3077$default'; then
    echo "Creating PostgreSQL database..."
    psql -c "CREATE DATABASE \"aniket3077\$default\";"
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p staticfiles
mkdir -p media

# Set correct permissions
echo "Setting permissions..."
chmod 755 staticfiles
chmod 755 media

# Touch the WSGI file to reload the application
echo "Reloading application..."
touch /var/www/aniket3077_pythonanywhere_com_wsgi.py

echo "Deployment completed successfully!" 