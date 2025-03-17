#!/bin/bash

# Check if .env file exists, create empty one if it doesn't
if [ ! -f /app/.env ]; then
    echo "Creating empty .env file as no mounted file was found"
    touch /app/.env
fi

# Create log directories for nginx if they don't exist
mkdir -p /var/log/nginx
touch /var/log/nginx/access.log
touch /var/log/nginx/error.log

# Start Next.js frontend in development mode
echo "Starting Next.js frontend in development mode..."
cd /app && npm run dev &
NEXT_PID=$!

# Start Flask backend server with auto-reload
echo "Starting Flask backend server with auto-reload..."
FLASK_APP=src/server.py FLASK_ENV=development PYTHONPATH=/app:/app/src python3 -m flask run --host=0.0.0.0 --reload &
FLASK_PID=$!

# Start tools server with auto-reload using watchdog
echo "Starting tools server with auto-reload..."
(cd /app && PYTHONPATH=/app:/app/src python3 -m watchdog.watchmedo auto-restart \
    --patterns="*.py" \
    --recursive \
    --directory="./src/tools" \
    -- python3 src/tools/server.py) &
TOOLS_PID=$!

# Give the services a moment to start
sleep 2

# Check if services started successfully
echo "Checking if services are running..."

if ! ps -p $NEXT_PID > /dev/null; then
    echo "WARNING: Next.js frontend failed to start"
fi

if ! ps -p $FLASK_PID > /dev/null; then
    echo "WARNING: Flask backend failed to start"
fi

if ! ps -p $TOOLS_PID > /dev/null; then
    echo "WARNING: Tools server failed to start"
fi

# Start nginx as our reverse proxy
echo "Starting nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!

echo "==================================================="
echo "Development server running with hot-reload enabled:"
echo " - Frontend: http://localhost/ (Next.js dev server)"
echo " - API: http://localhost/api/ (Flask with reload)"
echo " - Tools: http://localhost/tools/ (watchdog auto-restart)"
echo "==================================================="

# Function to handle termination
cleanup() {
    echo "Shutting down services..."
    kill -TERM $NEXT_PID 2>/dev/null
    kill -TERM $FLASK_PID 2>/dev/null
    kill -TERM $TOOLS_PID 2>/dev/null
    kill -TERM $NGINX_PID 2>/dev/null
    wait
    echo "All services terminated"
    exit 0
}

# Set up signal trapping
trap cleanup SIGTERM SIGINT

# Wait for all background processes to complete
wait

# Exit with the status of the last command
exit $?