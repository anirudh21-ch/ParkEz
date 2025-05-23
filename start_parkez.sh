#!/bin/bash

# Start ParkEZ Services
# This script starts all the necessary services for the ParkEZ application

# Get the current IP address
IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}')
echo "Current IP address: $IP_ADDRESS"

# Create logs directory if it doesn't exist
mkdir -p logs

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
NUMBERPLATE_PID=$!
echo "NumberPlate-Detection-Extraction app started with PID $NUMBERPLATE_PID"
cd ..

# Wait for the NumberPlate app to start
sleep 3

# Start the OCR adapter (port 5005)
echo "Starting OCR adapter on port 5005..."
python ocr_adapter.py > logs/ocr_adapter.log 2>&1 &
OCR_PID=$!
echo "OCR adapter started with PID $OCR_PID"

# Wait for the OCR adapter to start
sleep 3

# Start the backend server (port 5002)
echo "Starting backend server on port 5002..."
cd backend
npm start > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend server started with PID $BACKEND_PID"
cd ..

# Start the admin dashboard (port 3000)
echo "Starting admin dashboard on port 3000..."
cd admin
npm run dev > ../logs/admin.log 2>&1 &
ADMIN_PID=$!
echo "Admin dashboard started with PID $ADMIN_PID"
cd ..

echo "All services started successfully!"
echo "- NumberPlate-Detection-Extraction: http://$IP_ADDRESS:5001"
echo "- OCR Adapter: http://$IP_ADDRESS:5005"
echo "- Backend Server: http://$IP_ADDRESS:5002"
echo "- Admin Dashboard: http://$IP_ADDRESS:3000"
echo ""
echo "Process IDs:"
echo "- NumberPlate-Detection-Extraction: $NUMBERPLATE_PID"
echo "- OCR Adapter: $OCR_PID"
echo "- Backend Server: $BACKEND_PID"
echo "- Admin Dashboard: $ADMIN_PID"
echo ""
echo "To stop all services, run: ./stop_parkez.sh"
