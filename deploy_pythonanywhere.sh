#!/bin/bash

echo "Updating code from Git..."
cd ~/insideorgs
git pull

echo "Installing/Updating dependencies..."
pip install -r requirements.txt

echo "Running database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Reloading PythonAnywhere web app..."
touch /var/www/aniket3077_pythonanywhere_com_wsgi.py

echo "Deployment completed!" 