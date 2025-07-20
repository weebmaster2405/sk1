#!/bin/bash

# PythonAnywhere Deployment Script
# Run this script on PythonAnywhere to deploy the InsideOrgs application

echo "🚀 Starting InsideOrgs deployment on PythonAnywhere..."

# Set project directory
PROJECT_DIR="/home/aniket3077/insideorgs"
cd $PROJECT_DIR

echo "📁 Working directory: $PROJECT_DIR"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p staticfiles/
mkdir -p media/

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 $PROJECT_DIR/
chmod 755 $PROJECT_DIR/staticfiles/
chmod 755 $PROJECT_DIR/media/

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if not exists
echo "👤 Creating superuser (if needed)..."
python manage.py createsuperuser --noinput || echo "Superuser creation skipped (may already exist)"

echo "✅ Deployment completed!"
echo "🌐 Your app should be available at: https://aniket3077.pythonanywhere.com"
echo ""
echo "📋 Next steps:"
echo "1. Go to PythonAnywhere Web tab"
echo "2. Configure your web app"
echo "3. Update WSGI file to use production settings"
echo "4. Set environment variables"
echo "5. Click Reload" 