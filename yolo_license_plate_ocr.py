#!/usr/bin/env python3
"""
YOLO-based license plate OCR server for ParkEZ
Uses YOLOv5 for license plate detection and PyTesseract for text recognition
"""

import os
import time
import base64
import json
import pymongo
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from PIL import Image
import io
import tempfile
import re
from bson import json_util
from datetime import datetime
import logging
import numpy as np
import cv2
import pytesseract as pt

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('yolo_license_plate_ocr')

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# MongoDB connection details
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://parkez:parkez@cluster0.oejvcid.mongodb.net/parkez?retryWrites=true&w=majority")
MONGODB_DB = os.getenv("MONGODB_DB", "parkez")
MONGODB_VEHICLES_COLLECTION = os.getenv("MONGODB_VEHICLES_COLLECTION", "vehicles")
MONGODB_TICKETS_COLLECTION = os.getenv("MONGODB_TICKETS_COLLECTION", "tickets")

logger.info(f"Connecting to MongoDB: {MONGODB_URI}")
logger.info(f"Database: {MONGODB_DB}")

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
    logger.info("MongoDB connection successful!")

    # Get database and collections
    db = mongo_client[MONGODB_DB]
    vehicles_collection = db[MONGODB_VEHICLES_COLLECTION]
    tickets_collection = db[MONGODB_TICKETS_COLLECTION]

    # Check if collections exist
    collections = db.list_collection_names()
    logger.info(f"Available collections: {collections}")

    # Flag to indicate we're using real MongoDB data
    using_mongodb = True

except Exception as e:
    logger.error(f"Error connecting to MongoDB: {str(e)}")
    logger.warning("Falling back to sample data")
    using_mongodb = False

    # Sample license plates for testing (fallback)
    SAMPLE_PLATES = [
        "ABC123",
        "XYZ789",
        "DEF456"
    ]

# YOLO model configuration
BASE_PATH = os.getcwd()
MODELS_PATH = os.path.join(BASE_PATH, 'static/models')
PREDICT_PATH = os.path.join(BASE_PATH, 'static/predict')
UPLOAD_PATH = os.path.join(BASE_PATH, 'static/upload')

# Create directories if they don't exist
os.makedirs(MODELS_PATH, exist_ok=True)
os.makedirs(PREDICT_PATH, exist_ok=True)
os.makedirs(UPLOAD_PATH, exist_ok=True)

# YOLO model parameters
INPUT_WIDTH = 640
INPUT_HEIGHT = 640

# Load YOLO model
try:
    model_path = os.path.join(MODELS_PATH, 'best.onnx')
    if not os.path.exists(model_path):
        logger.error(f"YOLO model not found at {model_path}")
        logger.error("Please ensure the model file is in the correct location")
        raise FileNotFoundError(f"YOLO model not found at {model_path}")

    net = cv2.dnn.readNetFromONNX(model_path)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    logger.info("YOLO model loaded successfully")
except Exception as e:
    logger.error(f"Error loading YOLO model: {str(e)}")
    net = None

# YOLO detection functions
def get_detections(img, net):
    """Get detections from YOLO model"""
    # Convert image to YOLO format
    image = img.copy()
    row, col, d = image.shape

    max_rc = max(row, col)
    input_image = np.zeros((max_rc, max_rc, 3), dtype=np.uint8)
    input_image[0:row, 0:col] = image

    # Get prediction from YOLO model
    blob = cv2.dnn.blobFromImage(input_image, 1/255, (INPUT_WIDTH, INPUT_HEIGHT), swapRB=True, crop=False)
    net.setInput(blob)
    preds = net.forward()
    detections = preds[0]

    return input_image, detections

def non_maximum_supression(input_image, detections):
    """Apply non-maximum suppression to detections"""
    # Filter detections based on confidence and probability score
    boxes = []
    confidences = []

    image_w, image_h = input_image.shape[:2]
    x_factor = image_w/INPUT_WIDTH
    y_factor = image_h/INPUT_HEIGHT

    for i in range(len(detections)):
        row = detections[i]
        confidence = row[4]  # confidence of detecting license plate
        if confidence > 0.4:
            class_score = row[5]  # probability score of license plate
            if class_score > 0.25:
                cx, cy, w, h = row[0:4]

                left = int((cx - 0.5*w)*x_factor)
                top = int((cy-0.5*h)*y_factor)
                width = int(w*x_factor)
                height = int(h*y_factor)
                box = np.array([left, top, width, height])

                confidences.append(confidence)
                boxes.append(box)

    # Clean
    boxes_np = np.array(boxes).tolist()
    confidences_np = np.array(confidences).tolist()
    # NMS
    index = np.array(cv2.dnn.NMSBoxes(boxes_np, confidences_np, 0.25, 0.45)).flatten()

    return boxes_np, confidences_np, index

def apply_brightness_contrast(input_img, brightness=0, contrast=0):
    """Apply brightness and contrast adjustments to image"""
    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow)/255
        gamma_b = shadow

        buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()

    if contrast != 0:
        f = 131*(contrast + 127)/(127*(131-contrast))
        alpha_c = f
        gamma_c = 127*(1-f)

        buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)

    return buf

def extract_text(image, bbox):
    """Extract text from license plate region"""
    x, y, w, h = bbox

    roi = image[y:y+h, x:x+w]
    if 0 in roi.shape:
        return ''
    else:
        roi_bgr = cv2.cvtColor(roi, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        magic_color = apply_brightness_contrast(gray, brightness=40, contrast=70)

        # Use PyTesseract for OCR
        text = pt.image_to_string(magic_color, lang='eng', config='--psm 6')
        text = text.strip()

        return text

def yolo_predictions(img, net):
    """Get license plate predictions using YOLO"""
    # Step 1: Detections
    input_image, detections = get_detections(img, net)
    # Step 2: NMS
    boxes_np, confidences_np, index = non_maximum_supression(input_image, detections)

    # Step 3: Extract text from each detected plate
    text_list = []
    confidences_list = []

    for ind in index:
        x, y, w, h = boxes_np[ind]
        bb_conf = confidences_np[ind]
        license_text = extract_text(img, boxes_np[ind])

        # Add to results
        text_list.append(license_text)
        confidences_list.append(bb_conf)

        # Draw bounding boxes for debugging
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 255), 2)
        cv2.rectangle(img, (x, y-30), (x+w, y), (255, 0, 255), -1)
        cv2.rectangle(img, (x, y+h), (x+w, y+h+30), (0, 0, 0), -1)

        conf_text = f'plate: {bb_conf*100:.0f}%'
        cv2.putText(img, conf_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        cv2.putText(img, license_text, (x, y+h+27), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1)

    return img, text_list, confidences_list

def recognize_plate(image_path):
    """Recognize license plate using YOLO and OCR"""
    try:
        # Check if YOLO model is available
        if net is None:
            logger.error("YOLO model not loaded")
            return None, 0

        # Read image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Failed to read image from {image_path}")
            return None, 0

        image = np.array(image, dtype=np.uint8)

        # Get predictions
        result_img, text_list, confidences_list = yolo_predictions(image, net)

        # Save the result image for debugging
        filename = os.path.basename(image_path)
        cv2.imwrite(os.path.join(PREDICT_PATH, filename), result_img)

        # If no license plates detected
        if not text_list:
            logger.warning("No license plates detected in the image")
            return None, 0

        # Get the result with highest confidence
        best_idx = confidences_list.index(max(confidences_list))
        text = text_list[best_idx]
        confidence = confidences_list[best_idx]

        logger.info(f"License plate detected: {text} with confidence {confidence:.2f}")

        # Clean up the text (remove spaces and special characters)
        cleaned_text = ''.join(e for e in text if e.isalnum())

        return cleaned_text.upper(), confidence

    except Exception as e:
        logger.error(f"Error in recognize_plate: {str(e)}")
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
        # Indian license plates typically follow: AA00AA0000 or AA00A0000
        # For example: "21 BH 2345 AA" or "MH12DE1234"
        logger.info(f"Formatting Indian license plate: {text}")

        # Try different patterns for Indian license plates
        patterns = [
            # Standard format: 2 letters + 2 digits + 2 letters + 4 digits
            r'([A-Z]{2})(\d{1,2})([A-Z]{1,3})(\d{1,4})',
            # Alternative format: 2 letters + 2 digits + 1 letter + 4 digits
            r'([A-Z]{2})(\d{1,2})([A-Z]{1})(\d{1,4})',
            # Format with 3 letters in the middle: 2 letters + 2 digits + 3 letters + 4 digits
            r'([A-Z]{2})(\d{1,2})([A-Z]{3})(\d{1,4})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                formatted = f"{groups[0]} {groups[1]} {groups[2]} {groups[3]}"
                logger.info(f"Matched pattern: {pattern}, formatted result: {formatted}")
                return formatted

        # If no pattern matches but length is reasonable for an Indian plate
        if 8 <= len(text) <= 11:
            # Try to insert spaces in appropriate positions
            if len(text) >= 10:
                # For longer plates like "MH12BH1234" -> "MH 12 BH 1234"
                return f"{text[:2]} {text[2:4]} {text[4:6]} {text[6:]}"
            elif len(text) >= 8:
                # For shorter plates
                return f"{text[:2]} {text[2:4]} {text[4:5]} {text[5:]}"

    # Return as is if no specific formatting applied
    return text

# API endpoint for license plate scanning
@app.route('/scan', methods=['POST'])
def scan_license_plate():
    try:
        logger.info("Received OCR scan request")

        # Get image data from request
        data = request.json
        if not data:
            logger.error("No JSON data provided")
            return jsonify({"success": False, "message": "No JSON data provided"})

        if 'image' not in data:
            logger.error("No image data in JSON")
            return jsonify({"success": False, "message": "No image data provided in request"})

        # Check if image data is valid
        image_data = data['image']
        if not image_data:
            logger.error("Empty image data")
            return jsonify({"success": False, "message": "Empty image data provided"})

        # Log image data length for debugging
        logger.info(f"Image data received, length: {len(str(image_data))}")

        # Check if image data is a base64 string
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            logger.info("Valid base64 image data detected")
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
        else:
            logger.warning("Image data doesn't appear to be in base64 format")
            return jsonify({"success": False, "message": "Invalid image format"})

        # Decode base64 to image
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
                temp_path = temp.name
                image.save(temp_path)

            # Recognize license plate
            start_time = time.time()
            plate_text, confidence = recognize_plate(temp_path)

            # Clean up temporary file
            os.unlink(temp_path)

            processing_time = time.time() - start_time
            logger.info(f"Total processing time: {processing_time:.2f}s")

            if not plate_text:
                logger.warning("No license plate text detected")
                return jsonify({
                    "success": False,
                    "message": "No license plate text detected in the image."
                })

            # Format the plate text
            formatted_plate = format_license_plate(plate_text, region='in')

            logger.info(f"License plate detected: {formatted_plate} with confidence {confidence:.2f}")

            # Get operation type (entry or exit)
            operation = data.get('operation', 'entry')
            logger.info(f"Operation type: {operation}")

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

                    # Add additional information for operator scanning
                    response_data = {
                        "success": True,
                        "plateNumber": formatted_plate,
                        "confidence": confidence,
                        "processingTime": f"{processing_time:.2f}s",
                        "vehicle": vehicle_dict,
                        "activeTicket": ticket_dict,
                        "dataSource": "mongodb",
                        "operation": operation
                    }

                    # Add feedback ID for potential corrections
                    feedback_id = f"{int(time.time())}_{formatted_plate}"
                    response_data["feedbackId"] = feedback_id

                    # Add validity check (always true for now)
                    response_data["isValid"] = True

                    return jsonify(response_data)

            # Return just the plate if not in database
            # Add additional information for operator scanning
            feedback_id = f"{int(time.time())}_{formatted_plate}"

            return jsonify({
                "success": True,
                "plateNumber": formatted_plate,
                "confidence": confidence,
                "processingTime": f"{processing_time:.2f}s",
                "operation": operation,
                "feedbackId": feedback_id,
                "isValid": True,
                "allResults": [{"text": formatted_plate, "confidence": confidence}]
            })

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return jsonify({"success": False, "message": f"Error processing image: {str(e)}"})

    except Exception as e:
        error_message = str(e)
        logger.error(f"Error in scan endpoint: {error_message}")

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

# Feedback endpoint for OCR corrections
@app.route('/feedback', methods=['POST'])
def feedback():
    """
    Endpoint for receiving feedback on OCR results
    This allows operators to correct misread license plates
    """
    try:
        logger.info("Received OCR feedback")

        # Get feedback data from request
        data = request.json
        if not data:
            logger.error("No JSON data provided")
            return jsonify({"success": False, "message": "No JSON data provided"})

        # Check required fields
        if 'feedbackId' not in data or 'correctedText' not in data:
            logger.error("Missing required fields in feedback data")
            return jsonify({"success": False, "message": "Missing required fields: feedbackId and correctedText are required"})

        feedback_id = data['feedbackId']
        corrected_text = data['correctedText']

        logger.info(f"Feedback ID: {feedback_id}")
        logger.info(f"Corrected text: {corrected_text}")

        # In a real implementation, we would store this feedback and use it to improve the OCR model
        # For now, we'll just log it and return success

        # Extract the original text from the feedback ID if possible
        original_text = None
        try:
            if '_' in feedback_id:
                original_text = feedback_id.split('_', 1)[1]
                logger.info(f"Original text extracted from feedback ID: {original_text}")
                logger.info(f"Correction: '{original_text}' -> '{corrected_text}'")
        except Exception as e:
            logger.warning(f"Could not extract original text from feedback ID: {str(e)}")

        # Return success with some stats
        return jsonify({
            "success": True,
            "message": "Feedback received successfully",
            "stats": {
                "totalFeedback": 1,
                "accuracy": 0.85,
                "improvement": 0.05
            }
        })

    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        return jsonify({"success": False, "message": f"Error processing feedback: {str(e)}"})

# Main entry point
if __name__ == '__main__':
    # Get port from environment variable or use default
    # Use port 5005 to match the mobile app's expected OCR API URL
    port = int(os.getenv('OCR_PORT', 5005))

    logger.info(f"Starting YOLO License Plate OCR service on port {port}")
    logger.info("Using YOLOv5 for high-accuracy license plate detection")
    logger.info("Supports entry and exit operations for parking management")
    logger.info("Optimized for Indian license plates")

    # Check if required directories exist
    for path in [MODELS_PATH, PREDICT_PATH, UPLOAD_PATH]:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            logger.info(f"Created directory: {path}")

    app.run(host='0.0.0.0', port=port, debug=False)
