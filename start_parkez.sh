#!/bin/bash

# Start ParkEZ Services
# This script starts all the necessary services for the ParkEZ application

# Get the current IP address
IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}')
echo "Current IP address: $IP_ADDRESS"

# Function to check if a port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
    return $?
}

# Function to kill a process running on a specific port
kill_port() {
    echo "Killing process on port $1..."
    PID=$(lsof -t -i :$1)
    if [ ! -z "$PID" ]; then
        kill -9 $PID
        echo "Process on port $1 killed"
    else
        echo "No process found on port $1"
    fi
}

# Kill any existing processes on the required ports
for PORT in 5001 5002 5005; do
    if check_port $PORT; then
        echo "Port $PORT is in use. Killing process..."
        kill_port $PORT
    else
        echo "Port $PORT is available"
    fi
done

# Start the NumberPlate-Detection-Extraction app (port 5001)
echo "Starting NumberPlate-Detection-Extraction app on port 5001..."
cd NumberPlate-Detection-Extraction
python app.py > ../logs/numberplate_app.log 2>&1 &
echo "NumberPlate-Detection-Extraction app started with PID $!"
cd ..

# Wait for the NumberPlate app to start
sleep 3

# Start the OCR adapter (port 5005)
echo "Starting OCR adapter on port 5005..."
python ocr_adapter.py > logs/ocr_adapter.log 2>&1 &
echo "OCR adapter started with PID $!"

# Wait for the OCR adapter to start
sleep 3

# Start the backend server (port 5002)
echo "Starting backend server on port 5002..."
cd backend
npm start > ../logs/backend.log 2>&1 &
echo "Backend server started with PID $!"
cd ..

echo "All services started successfully!"
echo "- NumberPlate-Detection-Extraction: http://$IP_ADDRESS:5001"
echo "- OCR Adapter: http://$IP_ADDRESS:5005"
echo "- Backend Server: http://$IP_ADDRESS:5002"
echo ""
echo "To stop all services, run: ./stop_parkez.sh"
