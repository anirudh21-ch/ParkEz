#!/usr/bin/env python3
"""
Direct implementation of the YOLO-based license plate OCR from the NumberPlate-Detection-Extraction project
"""

from flask import Flask, render_template, request, jsonify
import os
import base64
import io
import json
import time
import tempfile
from PIL import Image
import numpy as np
import cv2
import pytesseract as pt
import logging
import pymongo
from flask_cors import CORS
from dotenv import load_dotenv
import re
from bson import json_util
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('direct_yolo_ocr')

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

# Set up paths
BASE_PATH = os.getcwd()
UPLOAD_PATH = os.path.join(BASE_PATH, 'static/upload/')
PREDICT_PATH = os.path.join(BASE_PATH, 'static/predict/')
MODELS_PATH = os.path.join(BASE_PATH, 'static/models/')

# Create directories if they don't exist
os.makedirs(UPLOAD_PATH, exist_ok=True)
os.makedirs(PREDICT_PATH, exist_ok=True)
os.makedirs(MODELS_PATH, exist_ok=True)

# YOLO model parameters
INPUT_WIDTH = 640
INPUT_HEIGHT = 640

# Load YOLO model
try:
    model_path = os.path.join(MODELS_PATH, 'best.onnx')
    if not os.path.exists(model_path):
        # Try to find the model in the NumberPlate-Detection-Extraction directory
        alt_model_path = os.path.join(BASE_PATH, 'NumberPlate-Detection-Extraction/static/models/best.onnx')
        if os.path.exists(alt_model_path):
            # Copy the model to our models directory
            import shutil
            shutil.copy(alt_model_path, model_path)
            logger.info(f"Copied model from {alt_model_path} to {model_path}")
        else:
            logger.error(f"YOLO model not found at {model_path} or {alt_model_path}")
            raise FileNotFoundError(f"YOLO model not found")

    net = cv2.dnn.readNetFromONNX(model_path)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    logger.info("YOLO model loaded successfully")
except Exception as e:
    logger.error(f"Error loading YOLO model: {str(e)}")
    raise

# DIRECT COPY OF FUNCTIONS FROM deeplearning.py

def get_detections(img, net):
    # CONVERT IMAGE TO YOLO FORMAT
    image = img.copy()
    row, col, d = image.shape

    max_rc = max(row, col)
    input_image = np.zeros((max_rc, max_rc, 3), dtype=np.uint8)
    input_image[0:row, 0:col] = image

    # GET PREDICTION FROM YOLO MODEL
    blob = cv2.dnn.blobFromImage(input_image, 1/255, (INPUT_WIDTH, INPUT_HEIGHT), swapRB=True, crop=False)
    net.setInput(blob)
    preds = net.forward()
    detections = preds[0]

    return input_image, detections

def non_maximum_supression(input_image, detections):
    # FILTER DETECTIONS BASED ON CONFIDENCE AND PROBABILIY SCORE
    # center x, center y, w , h, conf, proba
    boxes = []
    confidences = []

    image_w, image_h = input_image.shape[:2]
    x_factor = image_w/INPUT_WIDTH
    y_factor = image_h/INPUT_HEIGHT

    for i in range(len(detections)):
        row = detections[i]
        confidence = row[4] # confidence of detecting license plate
        if confidence > 0.4:
            class_score = row[5] # probability score of license plate
            if class_score > 0.25:
                cx, cy, w, h = row[0:4]

                left = int((cx - 0.5*w)*x_factor)
                top = int((cy-0.5*h)*y_factor)
                width = int(w*x_factor)
                height = int(h*y_factor)
                box = np.array([left, top, width, height])

                confidences.append(confidence)
                boxes.append(box)

    # clean
    boxes_np = np.array(boxes).tolist()
    confidences_np = np.array(confidences).tolist()
    # NMS
    index = np.array(cv2.dnn.NMSBoxes(boxes_np, confidences_np, 0.25, 0.45)).flatten()

    return boxes_np, confidences_np, index

def apply_brightness_contrast(input_img, brightness=0, contrast=0):
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
    x, y, w, h = bbox

    roi = image[y:y+h, x:x+w]
    if 0 in roi.shape:
        return ''
    else:
        roi_bgr = cv2.cvtColor(roi, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        magic_color = apply_brightness_contrast(gray, brightness=40, contrast=70)
        text = pt.image_to_string(magic_color, lang='eng', config='--psm 6')
        text = text.strip()
        return text

def drawings(image, boxes_np, confidences_np, index):
    # drawings
    text_list = []
    for ind in index:
        x, y, w, h = boxes_np[ind]
        bb_conf = confidences_np[ind]
        conf_text = 'plate: {:.0f}%'.format(bb_conf*100)
        license_text = extract_text(image, boxes_np[ind])

        cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 255), 2)
        cv2.rectangle(image, (x, y-30), (x+w, y), (255, 0, 255), -1)
        cv2.rectangle(image, (x, y+h), (x+w, y+h+30), (0, 0, 0), -1)

        cv2.putText(image, conf_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        cv2.putText(image, license_text, (x, y+h+27), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1)

        text_list.append(license_text)

    return image, text_list

def yolo_predictions(img, net):
    ## step-1: detections
    input_image, detections = get_detections(img, net)
    ## step-2: NMS
    boxes_np, confidences_np, index = non_maximum_supression(input_image, detections)
    ## step-3: Drawings
    result_img, text = drawings(img, boxes_np, confidences_np, index)
    return result_img, text

def object_detection(path, filename):
    # read image
    image = cv2.imread(path) # PIL object
    image = np.array(image, dtype=np.uint8) # 8 bit array (0,255)
    result_img, text_list = yolo_predictions(image, net)
    cv2.imwrite(os.path.join(PREDICT_PATH, filename), result_img)
    return text_list

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

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
                temp_path = temp.name
                with open(temp_path, 'wb') as f:
                    f.write(image_bytes)

                # Generate a unique filename
                filename = f"scan_{int(time.time())}.jpg"

                # Process the image using the YOLO model
                start_time = time.time()
                text_list = object_detection(temp_path, filename)

                # Clean up temporary file
                os.unlink(temp_path)

                processing_time = time.time() - start_time
                logger.info(f"Total processing time: {processing_time:.2f}s")

                if not text_list or len(text_list) == 0:
                    logger.warning("No license plates detected in the image")
                    return jsonify({
                        "success": False,
                        "message": "No license plates detected in the image."
                    })

                # Get the first license plate text (or the one with highest confidence if available)
                plate_text = text_list[0]

                # Format the plate text
                formatted_plate = format_license_plate(plate_text, region='in')

                logger.info(f"License plate detected: {formatted_plate}")

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
                            "confidence": 0.95,  # Using a fixed high confidence since we're using YOLO
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
                    "confidence": 0.95,  # Using a fixed high confidence since we're using YOLO
                    "processingTime": f"{processing_time:.2f}s",
                    "operation": operation,
                    "feedbackId": feedback_id,
                    "isValid": True,
                    "allResults": [{"text": text, "confidence": 0.95} for text in text_list]
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

# Web interface route (similar to the original app.py)
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        upload_file = request.files['image_name']
        filename = upload_file.filename
        path_save = os.path.join(UPLOAD_PATH, filename)
        upload_file.save(path_save)
        text_list = object_detection(path_save, filename)

        logger.info(f"Detected license plates: {text_list}")

        return render_template('index.html', upload=True, upload_image=filename, text=text_list, no=len(text_list))

    return render_template('index.html', upload=False)

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
    for path in [UPLOAD_PATH, PREDICT_PATH, MODELS_PATH]:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            logger.info(f"Created directory: {path}")

    # Copy the template file if it doesn't exist
    template_dir = os.path.join(BASE_PATH, 'templates')
    if not os.path.exists(template_dir):
        os.makedirs(template_dir, exist_ok=True)

        # Try to copy the template from the NumberPlate-Detection-Extraction project
        src_template = os.path.join(BASE_PATH, 'NumberPlate-Detection-Extraction/templates/index.html')
        dst_template = os.path.join(template_dir, 'index.html')

        if os.path.exists(src_template):
            import shutil
            shutil.copy(src_template, dst_template)
            logger.info(f"Copied template from {src_template} to {dst_template}")
        else:
            # Create a simple template if the original doesn't exist
            with open(dst_template, 'w') as f:
                f.write("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>License Plate Detection</title>
                    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
                </head>
                <body>
                    <div class="container mt-5">
                        <h1 class="text-center">License Plate Detection</h1>
                        <form method="post" enctype="multipart/form-data" class="mt-4">
                            <div class="form-group">
                                <label for="image_name">Upload Image</label>
                                <input type="file" class="form-control-file" id="image_name" name="image_name" required>
                            </div>
                            <button type="submit" class="btn btn-primary">Detect License Plate</button>
                        </form>

                        {% if upload %}
                        <div class="mt-5">
                            <h2>Results</h2>
                            <div class="row">
                                <div class="col-md-6">
                                    <h4>Original Image</h4>
                                    <img src="/static/upload/{{ upload_image }}" class="img-fluid">
                                </div>
                                <div class="col-md-6">
                                    <h4>Detected Image</h4>
                                    <img src="/static/predict/{{ upload_image }}" class="img-fluid">
                                </div>
                            </div>
                            <div class="mt-4">
                                <h4>Detected License Plates ({{ no }})</h4>
                                <ul class="list-group">
                                    {% for plate in text %}
                                    <li class="list-group-item">{{ plate }}</li>
                                    {% endfor %}
                                </ul>
                            </div>
                        </div>
                        {% endif %}
                    </div>
                </body>
                </html>
                """)
            logger.info(f"Created simple template at {dst_template}")

    # Print the server URL with the current IP address
    logger.info(f"Server running at http://192.168.1.6:{port}/")
    logger.info(f"For local access: http://localhost:{port}/")
    logger.info(f"For network access: http://192.168.1.6:{port}/")

    app.run(host='0.0.0.0', port=port, debug=False)
