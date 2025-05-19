import cv2
import numpy as np
import pytesseract
import re
from flask import Flask, request, jsonify
import base64
import os
import logging
import pymongo
from dotenv import load_dotenv
from flask_cors import CORS
from datetime import datetime, timedelta
from bson import ObjectId, json_util

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

# Sample data for initializing the database if empty
sample_vehicles = [
    {
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
        },
        "createdAt": datetime.now(),
        "updatedAt": datetime.now()
    },
    {
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
        },
        "createdAt": datetime.now(),
        "updatedAt": datetime.now()
    },
    {
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
        },
        "createdAt": datetime.now(),
        "updatedAt": datetime.now()
    }
]

sample_tickets = [
    {
        "vehicleNumber": "ABC123",
        "status": "active",
        "entryTime": datetime.now() - timedelta(hours=2),
        "zone": {
            "id": "z1",
            "name": "Downtown Parking",
            "hourlyRate": 2.5
        },
        "slotNumber": "A12",
        "createdAt": datetime.now(),
        "updatedAt": datetime.now()
    }
]

# Connect to MongoDB Atlas
# Get MongoDB connection details from environment variables
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')
MONGODB_VEHICLES_COLLECTION = os.getenv('MONGODB_VEHICLES_COLLECTION')
MONGODB_TICKETS_COLLECTION = os.getenv('MONGODB_TICKETS_COLLECTION')

logger.info(f"Connecting to MongoDB: {MONGODB_URI}")
logger.info(f"Database: {MONGODB_DB}")
logger.info(f"Collections: {MONGODB_VEHICLES_COLLECTION}, {MONGODB_TICKETS_COLLECTION}")

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

# Check if collections exist
collections = db.list_collection_names()
logger.info(f"Available collections: {collections}")

# Initialize collections with sample data if they don't exist or are empty
if MONGODB_VEHICLES_COLLECTION not in collections or vehicles_collection.count_documents({}) == 0:
    logger.info("Initializing vehicles collection with sample data")
    vehicles_collection.insert_many(sample_vehicles)
    logger.info(f"Inserted {len(sample_vehicles)} sample vehicles")

if MONGODB_TICKETS_COLLECTION not in collections or tickets_collection.count_documents({}) == 0:
    logger.info("Initializing tickets collection with sample data")
    tickets_collection.insert_many(sample_tickets)
    logger.info(f"Inserted {len(sample_tickets)} sample tickets")

logger.info("MongoDB setup complete")
using_mock_data = False

def preprocess_image(image):
    """Preprocess the image for better OCR results"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply threshold to get black and white image
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return thresh

def find_license_plate(image):
    """Find and extract the license plate region using contour detection"""
    # Create a copy of the image
    img_copy = image.copy()

    # Apply edge detection
    edges = cv2.Canny(img_copy, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Sort contours by area (largest first)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

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
    # Preprocess the image
    processed_img = preprocess_image(image)

    # Find license plate region
    plate_img = find_license_plate(processed_img)

    # Save the processed image for debugging (optional)
    # cv2.imwrite('processed_plate.jpg', plate_img)

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
            return most_common

        # If no results from the loop, try one more time with default settings
        text = pytesseract.image_to_string(plate_img)
        plate_text = re.sub(r'[^A-Z0-9]', '', text.upper().replace(' ', '').replace('\n', ''))

        if plate_text and len(plate_text) >= 3:
            logger.info(f"Fallback OCR result: {plate_text}")
            return plate_text

        # If still no valid result, check if we have any of our known plates in the text
        known_plates = ["ABC123", "XYZ789", "DEF456", "TEST123"]
        for known_plate in known_plates:
            if known_plate in text.upper():
                logger.info(f"Found known plate in text: {known_plate}")
                return known_plate

        logger.warning("No valid license plate text detected")
        return None
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        return None

def get_vehicle_info(plate_number):
    """Get vehicle information from MongoDB database"""
    try:
        # Find the vehicle in the MongoDB database
        vehicle = vehicles_collection.find_one({"vehicleNumber": plate_number})

        if vehicle:
            # Convert MongoDB document to JSON serializable format
            vehicle_dict = json_util.loads(json_util.dumps(vehicle))

            # Remove MongoDB _id field which is not JSON serializable
            if '_id' in vehicle_dict:
                del vehicle_dict['_id']

            # Convert datetime objects to ISO format strings
            if 'createdAt' in vehicle_dict:
                if isinstance(vehicle_dict['createdAt'], dict) and '$date' in vehicle_dict['createdAt']:
                    vehicle_dict['createdAt'] = vehicle_dict['createdAt']['$date']
                elif hasattr(vehicle_dict['createdAt'], 'isoformat'):
                    vehicle_dict['createdAt'] = vehicle_dict['createdAt'].isoformat()

            if 'updatedAt' in vehicle_dict:
                if isinstance(vehicle_dict['updatedAt'], dict) and '$date' in vehicle_dict['updatedAt']:
                    vehicle_dict['updatedAt'] = vehicle_dict['updatedAt']['$date']
                elif hasattr(vehicle_dict['updatedAt'], 'isoformat'):
                    vehicle_dict['updatedAt'] = vehicle_dict['updatedAt'].isoformat()

            return vehicle_dict

        return None
    except Exception as e:
        logger.error(f"Error getting vehicle info: {str(e)}")
        return None

def get_active_ticket(plate_number):
    """Get active ticket information from MongoDB database"""
    try:
        # Find active ticket for the vehicle in MongoDB
        ticket = tickets_collection.find_one({
            "vehicleNumber": plate_number,
            "status": "active"
        })

        if ticket:
            # Convert MongoDB document to JSON serializable format
            ticket_dict = json_util.loads(json_util.dumps(ticket))

            # Remove MongoDB _id field which is not JSON serializable
            if '_id' in ticket_dict:
                del ticket_dict['_id']

            # Convert datetime objects to ISO format strings
            if 'entryTime' in ticket_dict:
                if isinstance(ticket_dict['entryTime'], dict) and '$date' in ticket_dict['entryTime']:
                    ticket_dict['entryTime'] = ticket_dict['entryTime']['$date']
                elif hasattr(ticket_dict['entryTime'], 'isoformat'):
                    ticket_dict['entryTime'] = ticket_dict['entryTime'].isoformat()

            if 'createdAt' in ticket_dict:
                if isinstance(ticket_dict['createdAt'], dict) and '$date' in ticket_dict['createdAt']:
                    ticket_dict['createdAt'] = ticket_dict['createdAt']['$date']
                elif hasattr(ticket_dict['createdAt'], 'isoformat'):
                    ticket_dict['createdAt'] = ticket_dict['createdAt'].isoformat()

            if 'updatedAt' in ticket_dict:
                if isinstance(ticket_dict['updatedAt'], dict) and '$date' in ticket_dict['updatedAt']:
                    ticket_dict['updatedAt'] = ticket_dict['updatedAt']['$date']
                elif hasattr(ticket_dict['updatedAt'], 'isoformat'):
                    ticket_dict['updatedAt'] = ticket_dict['updatedAt'].isoformat()

            # Get vehicle information to include in the ticket
            vehicle = get_vehicle_info(plate_number)
            if vehicle:
                ticket_dict['vehicle'] = vehicle

            return ticket_dict

        return None
    except Exception as e:
        logger.error(f"Error getting active ticket: {str(e)}")
        return None

@app.route('/scan', methods=['POST'])
def scan_license_plate():
    """API endpoint to scan license plate from image"""
    try:
        logger.info("Received scan request")

        # Log request content type and headers
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request headers: {request.headers}")

        # Check if request has JSON data
        if not request.is_json:
            logger.error("Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400

        # Log request JSON data
        logger.info(f"Request JSON keys: {request.json.keys() if request.json else 'None'}")

        # Get the image data from the request
        if 'image' not in request.json:
            logger.error("No image provided in request")
            return jsonify({"error": "No image provided"}), 400

        # Get image data
        image_data = request.json['image']
        logger.info(f"Image data type: {type(image_data)}")

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
                prefix = image_data.split(',')[0]
                image_data = image_data.split(',')[1]
                logger.info(f"Removed prefix: {prefix}")
                logger.info(f"Image data length after prefix removal: {len(image_data)}")
        else:
            logger.error(f"Image data is not a string: {type(image_data)}")
            return jsonify({"error": "Image data must be a base64 string"}), 400

        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            logger.info(f"Decoded image bytes length: {len(image_bytes)}")

            # Convert to numpy array for OpenCV
            nparr = np.frombuffer(image_bytes, np.uint8)
            logger.info(f"Numpy array shape: {nparr.shape}")

            # Decode image
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                logger.error("Failed to decode image")
                return jsonify({"error": "Invalid image data"}), 400

            logger.info(f"Decoded image shape: {image.shape}")
        except Exception as decode_error:
            logger.error(f"Error decoding image: {str(decode_error)}")
            return jsonify({"error": f"Error decoding image: {str(decode_error)}"}), 400

        # Recognize license plate
        plate_number = recognize_license_plate(image)
        logger.info(f"Recognized plate number: {plate_number}")

        if not plate_number:
            return jsonify({
                "success": False,
                "message": "No license plate detected"
            }), 200

        # Get vehicle information from MongoDB
        vehicle = get_vehicle_info(plate_number)

        # Get active ticket information from MongoDB
        active_ticket = get_active_ticket(plate_number)

        # Log the results
        if vehicle:
            logger.info(f"Found vehicle: {plate_number} - {vehicle.get('make', '')} {vehicle.get('model', '')}")
        else:
            logger.info(f"No vehicle found for plate number: {plate_number}")

        if active_ticket:
            logger.info(f"Found active ticket for vehicle: {plate_number}")

        # Return the results
        return jsonify({
            "success": True,
            "plateNumber": plate_number,
            "vehicle": vehicle,
            "activeTicket": active_ticket
        }), 200

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/vehicles', methods=['GET'])
def get_all_vehicles():
    """API endpoint to get all vehicles"""
    try:
        # Get all vehicles from the MongoDB database
        cursor = vehicles_collection.find()

        # Convert MongoDB documents to JSON serializable format
        vehicles = json_util.loads(json_util.dumps(list(cursor)))

        # Remove MongoDB _id field and format datetime objects
        for vehicle in vehicles:
            if '_id' in vehicle:
                del vehicle['_id']

            # Convert datetime objects to ISO format strings
            if 'createdAt' in vehicle:
                if isinstance(vehicle['createdAt'], dict) and '$date' in vehicle['createdAt']:
                    vehicle['createdAt'] = vehicle['createdAt']['$date']
                elif hasattr(vehicle['createdAt'], 'isoformat'):
                    vehicle['createdAt'] = vehicle['createdAt'].isoformat()

            if 'updatedAt' in vehicle:
                if isinstance(vehicle['updatedAt'], dict) and '$date' in vehicle['updatedAt']:
                    vehicle['updatedAt'] = vehicle['updatedAt']['$date']
                elif hasattr(vehicle['updatedAt'], 'isoformat'):
                    vehicle['updatedAt'] = vehicle['updatedAt'].isoformat()

        return jsonify({
            "success": True,
            "data": vehicles
        }), 200
    except Exception as e:
        logger.error(f"Error getting vehicles: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/vehicles/<plate_number>', methods=['GET'])
def get_vehicle(plate_number):
    """API endpoint to get a specific vehicle"""
    try:
        # Get vehicle information
        vehicle = get_vehicle_info(plate_number)

        if not vehicle:
            return jsonify({"error": "Vehicle not found"}), 404

        return jsonify({
            "success": True,
            "data": vehicle
        }), 200
    except Exception as e:
        logger.error(f"Error getting vehicle: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/tickets/active/<plate_number>', methods=['GET'])
def get_active_ticket_endpoint(plate_number):
    """API endpoint to get active ticket for a vehicle"""
    try:
        # Get active ticket information
        ticket = get_active_ticket(plate_number)

        if not ticket:
            return jsonify({"error": "No active ticket found"}), 404

        return jsonify({
            "success": True,
            "data": ticket
        }), 200
    except Exception as e:
        logger.error(f"Error getting active ticket: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Check if Tesseract is installed
    try:
        pytesseract.get_tesseract_version()
        logger.info("Tesseract is installed and working")
    except Exception as e:
        logger.error(f"Tesseract is not installed or not working: {str(e)}")
        logger.error("Please install Tesseract OCR and make sure it's in your PATH")
        exit(1)

    # No need to initialize the database when using mock data
    logger.info("Using mock data, no database initialization needed")

    try:
        # Start the Flask app
        port = int(os.getenv("PORT", 5000))
        host = os.getenv("HOST", "0.0.0.0")
        debug = os.getenv("DEBUG", "True").lower() == "true"

        app.run(host=host, port=port, debug=debug)
    finally:
        # Close MongoDB connection when the app exits
        if 'mongo_client' in globals():
            mongo_client.close()
            logger.info("MongoDB connection closed")
        logger.info("Server shutting down")
