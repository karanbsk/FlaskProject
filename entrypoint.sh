#!/bin/sh
set -e  # Exit immediately if a command fails

echo "🚀 Starting Flask App in Production Mode..."

# Run database migrations
echo "📦 Applying database migrations..."
flask db upgrade

# Start the Flask app using Gunicorn
echo "✅ Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:8000 "app:create_app()"
