import os
import time
import base64
import random
import string
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Sample license plates for testing
SAMPLE_PLATES = [
    "ABC123",
    "XYZ789",
    "DEF456",
    "GHI789",
    "JKL012",
    "MNO345",
    "PQR678",
    "STU901",
    "VWX234",
    "YZA567"
]

# API endpoint for license plate scanning
@app.route('/scan', methods=['POST'])
def scan_license_plate():
    try:
        print("Received OCR scan request")

        # Get image data from request
        data = request.json
        if not data:
            print("Error: No JSON data provided")
            return jsonify({"success": False, "message": "No JSON data provided"})

        if 'image' not in data:
            print("Error: No image data in JSON")
            return jsonify({"success": False, "message": "No image data provided in request"})

        # Check if image data is valid
        image_data = data['image']
        if not image_data:
            print("Error: Empty image data")
            return jsonify({"success": False, "message": "Empty image data provided"})

        # Log image data length for debugging
        print(f"Image data received, length: {len(str(image_data))}")

        # Check if image data is a base64 string
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            print("Valid base64 image data detected")
        else:
            print("Warning: Image data doesn't appear to be in base64 format")

        # Simulate processing time
        time.sleep(0.5)

        # Always return success for testing
        # Select a random plate from the sample plates
        plate_number = random.choice(SAMPLE_PLATES)
        confidence = random.uniform(0.85, 0.98)

        print(f"License plate detected: {plate_number} with confidence {confidence:.2f}")

        return jsonify({
            "success": True,
            "plateNumber": plate_number,
            "confidence": confidence,
            "processingTime": "0.5s"
        })

    except Exception as e:
        error_message = str(e)
        print(f"Error in scan endpoint: {error_message}")

        # Provide more detailed error message
        if "JSON" in error_message:
            return jsonify({
                "success": False,
                "message": "Invalid JSON format in request",
                "error": error_message
            })
        else:
            return jsonify({
                "success": False,
                "message": "Server error processing image",
                "error": error_message
            })

# Main entry point
if __name__ == '__main__':
    # Get port from environment variable or use default
    port = 5002

    print(f"Starting simple OCR service on port {port}")
    print("This is a mock OCR service for testing purposes")
    print("It will return random license plates with 80% success rate")

    app.run(host='0.0.0.0', port=port, debug=False)
