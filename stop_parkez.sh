#!/bin/bash

# Stop ParkEZ Services
# This script stops all the services for the ParkEZ application

# Function to kill a process running on a specific port
kill_port() {
    echo "Stopping service on port $1..."
    PID=$(lsof -t -i :$1)
    if [ ! -z "$PID" ]; then
        kill -9 $PID
        echo "Process on port $1 stopped"
    else
        echo "No process found on port $1"
    fi
}

# Kill processes on the required ports
for PORT in 5001 5002 5005 3000; do
    kill_port $PORT
done

echo "All services stopped successfully!"
echo "You can check the logs in the logs directory:"
echo "- NumberPlate-Detection-Extraction: logs/numberplate_app.log"
echo "- OCR Adapter: logs/ocr_adapter.log"
echo "- Backend Server: logs/backend.log"
echo "- Admin Dashboard: logs/admin.log"
