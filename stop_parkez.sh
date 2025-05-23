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
for PORT in 5001 5002 5005; do
    kill_port $PORT
done

echo "All services stopped successfully!"
