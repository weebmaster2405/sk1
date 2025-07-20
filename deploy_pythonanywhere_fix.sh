#!/bin/bash

echo "🚀 PythonAnywhere Deployment Fix Script"
echo "======================================"

# Navigate to project directory
cd /home/aniket3077/insideorgs

echo "📁 Current directory: $(pwd)"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run this script from the project root."
    exit 1
fi

echo "✅ Found manage.py - we're in the right directory"

# Remove any existing SQLite database
echo "🗑️  Removing existing SQLite database (if any)..."
rm -f db.sqlite3

# Run migrations
echo "🔄 Running migrations..."
python manage.py migrate

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migration failed. Please check the error above."
    exit 1
fi

# Create superuser
echo "👤 Creating superuser..."
echo "Please enter the following details when prompted:"
python manage.py createsuperuser

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

if [ $? -eq 0 ]; then
    echo "✅ Static files collected successfully!"
else
    echo "❌ Static file collection failed."
    exit 1
fi

echo ""
echo "🎉 Deployment fix completed!"
echo "=========================="
echo "✅ Database: SQLite configured"
echo "✅ Migrations: Applied"
echo "✅ Static files: Collected"
echo "✅ Superuser: Created"
echo ""
echo "🌐 Your app should now work at: https://aniket3077.pythonanywhere.com"
echo ""
echo "📝 Next steps:"
echo "1. Reload your web app in PythonAnywhere dashboard"
echo "2. Test your application"
echo "3. If you need to make changes, edit files and reload again" 