#!/bin/bash

# Exit on error
set -e

# Install pyenv
echo "Installing pyenv..."
curl https://pyenv.run | bash
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

# Install Python
echo "Installing Python 3.9.18..."
pyenv install 3.9.18
pyenv global 3.9.18

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