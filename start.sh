#!/bin/bash

# Production startup script for Fly.io and Render.com
echo "Starting production server with Gunicorn..."

# Set default port if not provided
PORT=${PORT:-5000}

# Start Gunicorn with production settings
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app 