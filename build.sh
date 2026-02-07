#!/usr/bin/env bash
# exit on error
set -o errexit

echo "======================================"
echo "Starting Render.com build process..."
echo "======================================"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo ""
echo "📁 Collecting static files..."
python manage.py collectstatic --no-input --clear

echo ""
echo "======================================"
echo "✅ Build completed successfully!"
echo "======================================"
