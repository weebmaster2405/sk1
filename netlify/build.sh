#!/bin/bash

# Exit on error
set -e

# Install Python dependencies
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run Django collectstatic
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create necessary directories
mkdir -p staticfiles
mkdir -p media

echo "Build completed successfully!" 