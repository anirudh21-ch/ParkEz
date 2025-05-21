import os
import time
import base64
import json
import pymongo
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import cv2
import numpy as np
from PIL import Image
import io
import subprocess
import tempfile
import re
from bson import json_util

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# MongoDB connection details
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://learnanirudh1:anirudh2105@cluster0.oejvcid.mongodb.net/parkez?retryWrites=true&w=majority")
MONGODB_DB = os.getenv("MONGODB_DB", "parkez")
MONGODB_VEHICLES_COLLECTION = os.getenv("MONGODB_VEHICLES_COLLECTION", "vehicles")
MONGODB_TICKETS_COLLECTION = os.getenv("MONGODB_TICKETS_COLLECTION", "tickets")

print(f"Connecting to MongoDB: {MONGODB_URI}")
print(f"Database: {MONGODB_DB}")

# Connect to MongoDB
try:
    # Connect to MongoDB Atlas with SSL configuration
    mongo_client = pymongo.MongoClient(
        MONGODB_URI,
        ssl=True,
        tlsAllowInvalidCertificates=True,
        connectTimeoutMS=30000,
        socketTimeoutMS=None,
        connect=True,
        maxPoolSize=50
    )

    # Check if the connection was successful
    mongo_client.admin.command('ping')
    print("MongoDB connection successful!")

    # Get database and collections
    db = mongo_client[MONGODB_DB]
    vehicles_collection = db[MONGODB_VEHICLES_COLLECTION]
    tickets_collection = db[MONGODB_TICKETS_COLLECTION]

    # Check if collections exist
    collections = db.list_collection_names()
    print(f"Available collections: {collections}")

    # Flag to indicate we're using real MongoDB data
    using_mongodb = True

except Exception as e:
    print(f"Error connecting to MongoDB: {str(e)}")
    print("Falling back to sample data")
    using_mongodb = False

    # Sample license plates for testing (fallback)
    SAMPLE_PLATES = [
        "ABC123",
        "XYZ789",
        "DEF456"
    ]

# Function to run OpenALPR command line tool
def recognize_plate(image_path, region='in'):
    """
    Recognize license plate using OpenALPR command line tool

    Args:
        image_path: Path to the image file
        region: Region code for license plate format (us, eu, au, gb, kr, etc.)

    Returns:
        Tuple of (plate_number, confidence)
    """
    try:
        # Run OpenALPR command
        cmd = ['alpr', '-c', region, '-j', image_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse the JSON output
        output = json.loads(result.stdout)

        if not output['results']:
            return None, 0

        # Get the top result
        top_result = output['results'][0]
        plate = top_result['plate']
        confidence = float(top_result['confidence']) / 100.0  # Convert to 0-1 range

        return plate, confidence

    except subprocess.CalledProcessError as e:
        print(f"Error running OpenALPR: {e}")
        print(f"STDERR: {e.stderr}")
        return None, 0

    except json.JSONDecodeError as e:
        print(f"Error parsing OpenALPR output: {e}")
        return None, 0

    except Exception as e:
        print(f"Unexpected error in recognize_plate: {e}")
        return None, 0

# Function to preprocess image before OCR
def preprocess_image(image):
    """
    Preprocess image to improve OCR accuracy

    Args:
        image: OpenCV image

    Returns:
        Preprocessed image
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter to remove noise while keeping edges sharp
    blur = cv2.bilateralFilter(gray, 11, 17, 17)

    # Apply adaptive threshold
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 11, 2)

    # Find edges
    edged = cv2.Canny(thresh, 30, 200)

    # Find contours
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return image  # Return original if no contours found

    # Sort contours by area and keep the largest ones
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    # Find the contour with 4 corners (license plate)
    screenCnt = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * peri, True)
        if len(approx) == 4:
            screenCnt = approx
            break

    if screenCnt is None:
        return image  # Return original if no plate contour found

    # Create mask and crop
    mask = np.zeros(gray.shape, np.uint8)
    cv2.drawContours(mask, [screenCnt], 0, 255, -1)

    # Apply the mask
    masked = cv2.bitwise_and(image, image, mask=mask)

    return masked

# Function to format license plate text based on region
def format_license_plate(text, region='in'):
    """
    Format license plate text based on region

    Args:
        text: Raw license plate text
        region: Region code (in for India, us for USA, etc.)

    Returns:
        Formatted license plate text
    """
    # Remove any non-alphanumeric characters
    text = ''.join(e for e in text if e.isalnum())

    # Convert to uppercase
    text = text.upper()

    # Format based on region
    if region == 'in':
        # Indian license plates typically follow: AA00AA0000
        # Try to format if it matches the pattern
        if len(text) >= 8:
            # Check if we can identify the pattern
            match = re.search(r'([A-Z]{2})(\d{1,2})([A-Z]{1,3})(\d{1,4})', text)
            if match:
                groups = match.groups()
                return f"{groups[0]}{groups[1]}{groups[2]}{groups[3]}"

    # Return as is if no specific formatting applied
    return text

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
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
        else:
            print("Warning: Image data doesn't appear to be in base64 format")
            return jsonify({"success": False, "message": "Invalid image format"})

        # Decode base64 to image
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to OpenCV format
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Preprocess the image
            processed_image = preprocess_image(image_cv)

            # Save to temporary file (OpenALPR requires a file path)
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
                temp_path = temp.name
                cv2.imwrite(temp_path, processed_image)

            # Recognize license plate
            start_time = time.time()
            plate_text, confidence = recognize_plate(temp_path, region='in')  # Use 'in' for Indian plates
            processing_time = time.time() - start_time

            # Clean up temporary file
            os.unlink(temp_path)

            if not plate_text:
                print("No license plate detected")
                return jsonify({"success": False, "message": "No license plate detected in the image"})

            # Format the plate text
            formatted_plate = format_license_plate(plate_text, region='in')

            print(f"License plate detected: {formatted_plate} with confidence {confidence:.2f}")

            # Check if the plate exists in the database
            if using_mongodb:
                vehicle = vehicles_collection.find_one({"vehicleNumber": formatted_plate})

                if vehicle:
                    # Get vehicle details
                    vehicle_dict = json_util.loads(json_util.dumps(vehicle))
                    if '_id' in vehicle_dict:
                        vehicle_dict['id'] = str(vehicle_dict['_id'])
                        del vehicle_dict['_id']

                    # Get active ticket if any
                    active_ticket = tickets_collection.find_one({
                        "vehicleNumber": formatted_plate,
                        "status": "active"
                    })

                    if active_ticket:
                        ticket_dict = json_util.loads(json_util.dumps(active_ticket))
                        if '_id' in ticket_dict:
                            ticket_dict['id'] = str(ticket_dict['_id'])
                            del ticket_dict['_id']
                    else:
                        ticket_dict = None

                    return jsonify({
                        "success": True,
                        "plateNumber": formatted_plate,
                        "confidence": confidence,
                        "processingTime": f"{processing_time:.2f}s",
                        "vehicle": vehicle_dict,
                        "activeTicket": ticket_dict,
                        "dataSource": "mongodb"
                    })

            # Return just the plate if not in database
            return jsonify({
                "success": True,
                "plateNumber": formatted_plate,
                "confidence": confidence,
                "processingTime": f"{processing_time:.2f}s"
            })

        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return jsonify({"success": False, "message": f"Error processing image: {str(e)}"})

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
    port = int(os.getenv('PORT', 5004))

    print(f"Starting OpenALPR OCR service on port {port}")
    print("This service uses OpenALPR for high-accuracy license plate recognition")

    app.run(host='0.0.0.0', port=port, debug=False)
