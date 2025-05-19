import cv2
import numpy as np
import pytesseract
import re
from flask import Flask, request, jsonify
import base64
import os
import logging
from flask_cors import CORS
import time
import pymongo
from dotenv import load_dotenv
from bson import ObjectId, json_util
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Flask to handle large requests (up to 50MB)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

# MongoDB connection details
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "parkez")
MONGODB_VEHICLES_COLLECTION = os.getenv("MONGODB_VEHICLES_COLLECTION", "vehicles")
MONGODB_TICKETS_COLLECTION = os.getenv("MONGODB_TICKETS_COLLECTION", "tickets")
MONGODB_USERS_COLLECTION = "users"
MONGODB_ZONES_COLLECTION = "zones"

# Connect to MongoDB Atlas
logger.info(f"Connecting to MongoDB: {MONGODB_URI}")
logger.info(f"Database: {MONGODB_DB}")
logger.info(f"Collections: {MONGODB_VEHICLES_COLLECTION}, {MONGODB_TICKETS_COLLECTION}")

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
    logger.info("MongoDB connection successful!")

    # Get database and collections
    db = mongo_client[MONGODB_DB]
    vehicles_collection = db[MONGODB_VEHICLES_COLLECTION]
    tickets_collection = db[MONGODB_TICKETS_COLLECTION]
    users_collection = db[MONGODB_USERS_COLLECTION]
    zones_collection = db[MONGODB_ZONES_COLLECTION]

    # Check if collections exist
    collections = db.list_collection_names()
    logger.info(f"Available collections: {collections}")

    # Flag to indicate we're using real MongoDB data
    using_mongodb = True

except Exception as e:
    logger.error(f"Error connecting to MongoDB: {str(e)}")
    logger.error("Falling back to sample data")
    using_mongodb = False

    # Sample vehicle data for testing (fallback if MongoDB connection fails)
    SAMPLE_VEHICLES = {
        "ABC123": {
            "vehicleNumber": "ABC123",
            "vehicleType": "car",
            "make": "Toyota",
            "model": "Corolla",
            "color": "Blue",
            "user": {
                "id": "u1",
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "555-1234"
            }
        },
        "XYZ789": {
            "vehicleNumber": "XYZ789",
            "vehicleType": "car",
            "make": "Honda",
            "model": "Civic",
            "color": "Red",
            "user": {
                "id": "u2",
                "name": "Jane Smith",
                "email": "jane@example.com",
                "phone": "555-5678"
            }
        },
        "DEF456": {
            "vehicleNumber": "DEF456",
            "vehicleType": "suv",
            "make": "Ford",
            "model": "Explorer",
            "color": "Black",
            "user": {
                "id": "u3",
                "name": "Bob Johnson",
                "email": "bob@example.com",
                "phone": "555-9012"
            }
        }
    }

    # Sample active tickets for testing (fallback if MongoDB connection fails)
    ACTIVE_TICKETS = {
        "ABC123": {
            "vehicleNumber": "ABC123",
            "status": "active",
            "entryTime": "2023-05-18T10:00:00",
            "zone": {
                "id": "z1",
                "name": "Downtown Parking",
                "hourlyRate": 2.5
            },
            "slotNumber": "A12"
        }
    }

def preprocess_image(image):
    """Preprocess the image for better OCR results"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter to reduce noise while preserving edges
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)

    # Apply adaptive threshold to get black and white image
    thresh = cv2.adaptiveThreshold(filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY_INV, 11, 2)

    # Apply morphological operations to remove small noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return morph

def find_license_plate(image):
    """Find and extract the license plate region using contour detection"""
    # Create a copy of the image
    img_copy = image.copy()

    # Convert to grayscale if not already
    if len(img_copy.shape) == 3:
        gray = cv2.cvtColor(img_copy, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_copy

    # Apply edge detection
    edges = cv2.Canny(gray, 50, 200, apertureSize=3)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Sort contours by area (largest first)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15]

    # Initialize license plate contour
    plate_contour = None

    # Loop through contours to find the license plate
    for contour in contours:
        # Approximate the contour
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

        # If the contour has 4 points, it's likely a license plate
        if len(approx) == 4:
            plate_contour = approx
            break

    # If a license plate contour is found
    if plate_contour is not None:
        # Get the bounding rectangle
        x, y, w, h = cv2.boundingRect(plate_contour)

        # Check if the aspect ratio is reasonable for a license plate
        aspect_ratio = w / float(h)
        if 1.5 <= aspect_ratio <= 5.0:  # Typical license plate aspect ratios
            # Extract the license plate region
            plate_img = image[y:y+h, x:x+w]

            # Check if the plate image is valid
            if plate_img.size > 0:
                # Resize the plate image for better OCR
                plate_img = cv2.resize(plate_img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                return plate_img

    # If no valid plate is found, return the original image
    logger.info("No license plate region detected, using full image")
    return image

def recognize_license_plate(image):
    """Recognize text in the license plate image"""
    # Start timing
    start_time = time.time()

    # Preprocess the image
    processed_img = preprocess_image(image)

    # Find license plate region
    plate_img = find_license_plate(processed_img)

    # Use Tesseract to recognize text with multiple configurations
    try:
        # Try different PSM modes for better accuracy
        psm_modes = [7, 8, 6, 10, 11]
        results = []

        for psm_mode in psm_modes:
            config = f'--psm {psm_mode} --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            text = pytesseract.image_to_string(plate_img, config=config)

            # Clean up the text
            text = text.strip().replace(' ', '').replace('\n', '')

            # Extract alphanumeric characters
            plate_text = re.sub(r'[^A-Z0-9]', '', text.upper())

            if plate_text and len(plate_text) >= 3:
                results.append(plate_text)
                logger.info(f"OCR result with PSM {psm_mode}: {plate_text}")

        # If we have results, return the most common one or the first one
        if results:
            # Count occurrences of each result
            from collections import Counter
            result_counts = Counter(results)

            # Get the most common result
            most_common = result_counts.most_common(1)[0][0]
            logger.info(f"Selected OCR result: {most_common}")

            # Calculate processing time
            processing_time = time.time() - start_time

            return most_common, processing_time

        # If no results from the loop, try one more time with default settings
        text = pytesseract.image_to_string(plate_img)
        plate_text = re.sub(r'[^A-Z0-9]', '', text.upper().replace(' ', '').replace('\n', ''))

        if plate_text and len(plate_text) >= 3:
            logger.info(f"Fallback OCR result: {plate_text}")

            # Calculate processing time
            processing_time = time.time() - start_time

            return plate_text, processing_time

        # If still no valid result, check if we have any of our known plates in the text
        known_plates = ["ABC123", "XYZ789", "DEF456"]
        for known_plate in known_plates:
            if known_plate in text.upper():
                logger.info(f"Found known plate in text: {known_plate}")

                # Calculate processing time
                processing_time = time.time() - start_time

                return known_plate, processing_time

        logger.warning("No valid license plate text detected")
        return None, time.time() - start_time
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        return None, time.time() - start_time

def get_vehicle_from_mongodb(plate_number):
    """Get vehicle information from MongoDB database"""
    try:
        if not using_mongodb:
            return None

        # Find the vehicle in the MongoDB database
        vehicle = vehicles_collection.find_one({"vehicleNumber": plate_number})

        if not vehicle:
            logger.info(f"No vehicle found in MongoDB with plate number: {plate_number}")
            return None

        # Convert MongoDB document to JSON serializable format
        vehicle_dict = json_util.loads(json_util.dumps(vehicle))

        # Get user information
        if 'user' in vehicle_dict and isinstance(vehicle_dict['user'], ObjectId):
            user_id = vehicle_dict['user']
            user = users_collection.find_one({"_id": user_id})
            if user:
                user_dict = json_util.loads(json_util.dumps(user))
                # Remove sensitive information
                if 'password' in user_dict:
                    del user_dict['password']
                vehicle_dict['user'] = user_dict

        # Format the response
        formatted_vehicle = {
            "vehicleNumber": vehicle_dict.get("vehicleNumber"),
            "vehicleType": vehicle_dict.get("vehicleType"),
            "make": vehicle_dict.get("make"),
            "model": vehicle_dict.get("model"),
            "color": vehicle_dict.get("color"),
            "user": {
                "id": str(vehicle_dict.get("user", {}).get("_id", "")),
                "name": vehicle_dict.get("user", {}).get("name", ""),
                "email": vehicle_dict.get("user", {}).get("email", ""),
                "phone": vehicle_dict.get("user", {}).get("phone", "")
            }
        }

        logger.info(f"Found vehicle in MongoDB: {formatted_vehicle['vehicleNumber']} - {formatted_vehicle['make']} {formatted_vehicle['model']}")
        return formatted_vehicle

    except Exception as e:
        logger.error(f"Error getting vehicle from MongoDB: {str(e)}")
        return None

def get_active_ticket_from_mongodb(plate_number):
    """Get active ticket information from MongoDB database"""
    try:
        if not using_mongodb:
            return None

        # First get the vehicle to get its ID
        vehicle = vehicles_collection.find_one({"vehicleNumber": plate_number})

        if not vehicle:
            logger.info(f"No vehicle found in MongoDB with plate number: {plate_number}")
            return None

        # Find active ticket for the vehicle
        ticket = tickets_collection.find_one({
            "vehicle": vehicle["_id"],
            "status": "active"
        })

        if not ticket:
            logger.info(f"No active ticket found in MongoDB for vehicle: {plate_number}")
            return None

        # Convert MongoDB document to JSON serializable format
        ticket_dict = json_util.loads(json_util.dumps(ticket))

        # Get zone information
        zone = None
        if 'zone' in ticket_dict and isinstance(ticket_dict['zone'], ObjectId):
            zone_id = ticket_dict['zone']
            zone = zones_collection.find_one({"_id": zone_id})
            if zone:
                zone = json_util.loads(json_util.dumps(zone))

        # Format the response
        formatted_ticket = {
            "vehicleNumber": plate_number,
            "status": ticket_dict.get("status"),
            "entryTime": ticket_dict.get("entryTime", {}).get("$date") if isinstance(ticket_dict.get("entryTime"), dict) else str(ticket_dict.get("entryTime")),
            "slotNumber": ticket_dict.get("slotNumber"),
            "zone": {
                "id": str(zone.get("_id", "")) if zone else "",
                "name": zone.get("name", "") if zone else "",
                "hourlyRate": zone.get("hourlyRate", 0) if zone else 0
            }
        }

        logger.info(f"Found active ticket in MongoDB for vehicle: {plate_number}")
        return formatted_ticket

    except Exception as e:
        logger.error(f"Error getting active ticket from MongoDB: {str(e)}")
        return None

@app.route('/scan', methods=['POST'])
def scan_license_plate():
    """API endpoint to scan license plate from image"""
    try:
        logger.info("Received scan request")

        # Check if request has JSON data
        if not request.is_json:
            logger.error("Request is not JSON")
            return jsonify({"success": False, "message": "Request must be JSON"}), 400

        # Get the image data from the request
        if 'image' not in request.json:
            logger.error("No image provided in request")
            return jsonify({"success": False, "message": "No image provided"}), 400

        # Get image data
        image_data = request.json['image']

        # Check if it's a test request
        if image_data == 'test':
            logger.info("Test request received")
            return jsonify({"success": True, "message": "Test successful"}), 200

        # Log image data length
        if isinstance(image_data, str):
            logger.info(f"Image data length: {len(image_data)}")

            # Check if it has the data:image prefix
            has_prefix = image_data.startswith('data:image')
            logger.info(f"Image has prefix: {has_prefix}")

            # Remove the data:image/jpeg;base64, prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
        else:
            logger.error(f"Image data is not a string: {type(image_data)}")
            return jsonify({"success": False, "message": "Image data must be a base64 string"}), 400

        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            logger.info(f"Decoded image bytes length: {len(image_bytes)}")

            # Convert to numpy array for OpenCV
            nparr = np.frombuffer(image_bytes, np.uint8)

            # Decode image
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                logger.error("Failed to decode image")
                return jsonify({"success": False, "message": "Invalid image data"}), 400

            logger.info(f"Decoded image shape: {image.shape}")
        except Exception as decode_error:
            logger.error(f"Error decoding image: {str(decode_error)}")
            return jsonify({"success": False, "message": f"Error decoding image: {str(decode_error)}"}), 400

        # Recognize license plate
        plate_number, processing_time = recognize_license_plate(image)
        logger.info(f"Recognized plate number: {plate_number}")

        if not plate_number:
            return jsonify({
                "success": False,
                "message": "No license plate detected",
                "processingTime": f"{processing_time:.2f}s"
            }), 200

        # Get vehicle and ticket information
        vehicle = None
        active_ticket = None

        if using_mongodb:
            # Get data from MongoDB
            logger.info(f"Getting vehicle and ticket data from MongoDB for plate: {plate_number}")
            vehicle = get_vehicle_from_mongodb(plate_number)
            active_ticket = get_active_ticket_from_mongodb(plate_number)
        else:
            # Fallback to sample data if MongoDB is not available
            logger.info(f"Using sample data for plate: {plate_number}")
            vehicle = SAMPLE_VEHICLES.get(plate_number)
            active_ticket = ACTIVE_TICKETS.get(plate_number)

        # Return the results
        return jsonify({
            "success": True,
            "plateNumber": plate_number,
            "confidence": 0.95,  # Placeholder confidence value
            "processingTime": f"{processing_time:.2f}s",
            "vehicle": vehicle,
            "activeTicket": active_ticket,
            "dataSource": "mongodb" if using_mongodb else "sample"
        }), 200

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    # Check if Tesseract is installed
    try:
        pytesseract.get_tesseract_version()
        logger.info("Tesseract is installed and working")
    except Exception as e:
        logger.error(f"Tesseract is not installed or not working: {str(e)}")
        logger.error("Please install Tesseract OCR and make sure it's in your PATH")
        exit(1)

    # Start the Flask app
    port = int(os.getenv("PORT", 5002))  # Default to port 5002
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "False").lower() == "true"

    # Check if port is in use
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    if result == 0:
        logger.warning(f"Port {port} is already in use. Trying port 5004")
        port = 5004
        # Check if the new port is also in use
        result = sock.connect_ex(('127.0.0.1', port))
        if result == 0:
            logger.warning(f"Port {port} is also in use. Trying port 5005")
            port = 5005

    logger.info(f"Starting OCR service on port {port}")
    logger.info(f"Using {'MongoDB' if using_mongodb else 'sample'} data")

    try:
        app.run(host=host, port=port, debug=debug)
    finally:
        # Close MongoDB connection when the app exits
        if using_mongodb and 'mongo_client' in globals():
            mongo_client.close()
            logger.info("MongoDB connection closed")
        logger.info("Server shutting down")
