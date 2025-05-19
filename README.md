# ParkEz - Smart Parking System

ParkEz is a smart parking platform with a React Native mobile app for users and operators, and a Python backend for license plate recognition.

## System Components

1. **Mobile App (React Native with Expo)**
   - User interface for parking users and operators
   - Camera integration for license plate scanning
   - Real-time parking status and management

2. **OCR Backend (Python)**
   - License plate recognition using OpenCV and Tesseract OCR
   - Vehicle database management
   - REST API for mobile app integration

## Setup Instructions

### Prerequisites

- Node.js (v14 or later)
- Python 3.7 or later
- Tesseract OCR
- Expo CLI

### Setting up the OCR Backend

1. Install Tesseract OCR:
   - **macOS**: `brew install tesseract`
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download and install from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the OCR server:
   ```bash
   python license_plate_ocr.py
   ```
   The server will start on http://localhost:5000

4. (Optional) For testing with the mobile app on a real device, you'll need to expose your local server to the internet. You can use ngrok:
   ```bash
   ngrok http 5000
   ```
   Note the HTTPS URL provided by ngrok, you'll need to update it in the mobile app.

### Setting up the Mobile App

1. Navigate to the mobile app directory:
   ```bash
   cd parkez-mobile
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Update the OCR API URL in `src/screens/operator/ScanScreen.tsx`:
   - Find the line with `const OCR_API_URL = 'http://your-backend-url.com/scan';`
   - Replace it with your actual backend URL (e.g., the ngrok URL if testing with a real device)
   - Uncomment the fetch code block to use the real API

4. Start the Expo development server:
   ```bash
   npx expo start
   ```

5. Use the Expo Go app on your mobile device to scan the QR code and open the app

## Using the App

### For Operators

1. Log in as an operator
2. Navigate to the "Scan" tab
3. Tap the camera button to scan a license plate
4. Position the license plate within the frame and tap the capture button
5. The app will send the image to the OCR backend for processing
6. If a license plate is detected, the app will display the vehicle information
7. For entry, you can check in the vehicle
8. For exit, you can check out the vehicle and see the parking fee

### OCR Camera Integration

The app uses a real camera integration with the following features:

1. **Real-time Camera Access**: Uses Expo Camera to access the device's camera
2. **License Plate Detection**: Captures images and sends them to the Python OCR backend
3. **Dynamic Results**: Shows actual vehicle information based on the recognized plate
4. **Fallback Mechanism**: If the server is unavailable, falls back to local recognition
5. **Error Handling**: Provides clear feedback for various error scenarios

### For Users

1. Log in as a user
2. View your active parking tickets
3. See parking history and details

## MongoDB Database Setup

The system uses MongoDB to store vehicle and ticket information. Here's how to set it up:

### Local MongoDB Setup

1. Install MongoDB:
   - **macOS**: `brew install mongodb-community`
   - **Ubuntu/Debian**: `sudo apt-get install mongodb`
   - **Windows**: Download and install from [MongoDB website](https://www.mongodb.com/try/download/community)

2. Start MongoDB:
   - **macOS/Linux**: `sudo systemctl start mongod` or `brew services start mongodb-community`
   - **Windows**: MongoDB should run as a service after installation

3. The system will automatically initialize the database with sample data when you run the OCR backend.

### Sample Data

The system is pre-configured with the following license plates:

- **ABC123**: Toyota Corolla (Blue) - Owner: John Doe
- **XYZ789**: Honda Civic (Red) - Owner: Jane Smith
- **DEF456**: Ford Explorer (Black) - Owner: Bob Johnson

### Adding More Vehicles

To add more vehicles to the database, you can:

1. Edit the `SAMPLE_VEHICLES` list in `init_db.py` and restart the server
2. Use MongoDB Compass or another MongoDB client to add entries directly
3. Create an admin API endpoint to add vehicles (not included in this version)

### MongoDB Connection

The connection details are stored in the `.env` file. By default, it connects to a local MongoDB instance:

```
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=parkez
```

For production, you should use a hosted MongoDB service like MongoDB Atlas.

## Troubleshooting

- **OCR not working properly**: Make sure Tesseract is installed correctly and in your PATH
- **Camera not working**: Ensure you've granted camera permissions to the app
- **API connection issues**: Check that your backend URL is correct and the server is running

## Next Steps

- Implement user authentication
- Add pre-booking features
- Integrate with payment gateways
- Add real-time parking space availability
