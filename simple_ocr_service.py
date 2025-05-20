import os
import time
import base64
import random
import pymongo
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from bson import json_util

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# MongoDB connection details
MONGODB_URI = "mongodb+srv://learnanirudh1:anirudh2105@cluster0.oejvcid.mongodb.net/parkez?retryWrites=true&w=majority"
MONGODB_DB = "parkez"
MONGODB_VEHICLES_COLLECTION = "vehicles"
MONGODB_TICKETS_COLLECTION = "tickets"

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

        # In a real implementation, we would process the image here
        # For now, we'll select a plate from the database or use a sample
        if using_mongodb:
            # Get a random vehicle from MongoDB
            vehicles = list(vehicles_collection.find().limit(10))
            if vehicles:
                # Select a random vehicle
                vehicle = random.choice(vehicles)
                plate_number = vehicle.get('vehicleNumber', 'ABC123')

                # Get vehicle details
                vehicle_dict = json_util.loads(json_util.dumps(vehicle))
                if '_id' in vehicle_dict:
                    del vehicle_dict['_id']

                # Get active ticket if any
                active_ticket = tickets_collection.find_one({
                    "vehicleNumber": plate_number,
                    "status": "active"
                })

                if active_ticket:
                    ticket_dict = json_util.loads(json_util.dumps(active_ticket))
                    if '_id' in ticket_dict:
                        del ticket_dict['_id']
                else:
                    ticket_dict = None

                print(f"License plate detected from MongoDB: {plate_number}")

                return jsonify({
                    "success": True,
                    "plateNumber": plate_number,
                    "confidence": 0.95,
                    "processingTime": "0.5s",
                    "vehicle": vehicle_dict,
                    "activeTicket": ticket_dict,
                    "dataSource": "mongodb"
                })
            else:
                # Fallback to sample data if no vehicles in database
                plate_number = "ABC123"
        else:
            # Use sample data
            plate_number = random.choice(SAMPLE_PLATES)

        confidence = random.uniform(0.85, 0.98)
        print(f"License plate detected: {plate_number} with confidence {confidence:.2f}")

        return jsonify({
            "success": True,
            "plateNumber": plate_number,
            "confidence": confidence,
            "processingTime": "0.5s",
            "dataSource": "sample"
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
    port = 5004

    print(f"Starting simple OCR service on port {port}")
    print("This is a mock OCR service for testing purposes")
    print("It will connect to MongoDB for vehicle data")

    app.run(host='0.0.0.0', port=port, debug=False)
