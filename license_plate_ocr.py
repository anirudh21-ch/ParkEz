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
import pytesseract
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

# Function to preprocess image for better license plate detection
def preprocess_image(image):
    """
    Preprocess image to improve license plate detection

    Args:
        image: OpenCV image

    Returns:
        Preprocessed image and detected license plate region
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
        return gray, None  # Return original if no contours found

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
        # Try to find any rectangular contour if we can't find a perfect 4-corner one
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = float(w) / h
            # License plates typically have an aspect ratio between 2 and 5
            if 1.5 <= aspect_ratio <= 5:
                screenCnt = cv2.boxPoints(cv2.minAreaRect(c))
                screenCnt = np.int0(screenCnt)
                break

    if screenCnt is None:
        return gray, None  # Return original if no plate contour found

    # Get the bounding rectangle
    x, y, w, h = cv2.boundingRect(screenCnt)

    # Crop the image to the license plate region
    plate_region = gray[max(0, y-5):min(gray.shape[0], y+h+5), max(0, x-5):min(gray.shape[1], x+w+5)]

    if plate_region.size == 0:
        return gray, None

    # Resize for better OCR
    plate_region = cv2.resize(plate_region, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Apply threshold again
    _, plate_region = cv2.threshold(plate_region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return gray, plate_region

# Function to recognize text from license plate image
def recognize_text(plate_image):
    """
    Recognize text from license plate image using Tesseract OCR

    Args:
        plate_image: License plate image

    Returns:
        Tuple of (plate_text, confidence)
    """
    if plate_image is None:
        return None, 0

    # Configure Tesseract to focus on license plate characters
    custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    try:
        # Get OCR result
        text = pytesseract.image_to_string(plate_image, config=custom_config)

        # Clean the text
        text = ''.join(e for e in text if e.isalnum())

        if not text:
            return None, 0

        # Get confidence
        data = pytesseract.image_to_data(plate_image, config=custom_config, output_type=pytesseract.Output.DICT)

        # Calculate average confidence for all detected text
        confidences = [int(conf) for conf in data['conf'] if conf != '-1']
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return text, avg_confidence / 100.0  # Convert to 0-1 range

    except Exception as e:
        print(f"Error in OCR: {str(e)}")
        return None, 0

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
    if not text:
        return text

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

            # Preprocess the image and detect license plate
            start_time = time.time()
            _, plate_region = preprocess_image(image_cv)

            if plate_region is None:
                print("No license plate region detected")
                # Try with the full image as fallback
                plate_text, confidence = recognize_text(cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY))
            else:
                # Recognize text from the plate region
                plate_text, confidence = recognize_text(plate_region)

            processing_time = time.time() - start_time

            if not plate_text:
                print("No license plate text detected")
                return jsonify({"success": False, "message": "No license plate text detected in the image"})

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
    port = 5004

    print(f"Starting License Plate OCR service on port {port}")
    print("This service uses OpenCV and Tesseract OCR for license plate recognition")
    print("Optimized for Indian license plates")

    app.run(host='0.0.0.0', port=port, debug=False)
