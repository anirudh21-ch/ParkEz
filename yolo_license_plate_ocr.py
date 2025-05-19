import os
import cv2
import numpy as np
import torch
import easyocr
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import re
import logging
from PIL import Image
import io

# Disable YOLOv5 dependencies that are not needed for our use case
os.environ['PYTHONPATH'] = os.getcwd()
os.environ['YOLO_NO_ANALYTICS'] = '1'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load YOLOv5 model
def load_model():
    try:
        # Load YOLOv5 small model
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

        # Set model parameters
        model.conf = 0.25  # Confidence threshold
        model.iou = 0.45   # IoU threshold
        model.classes = [2]  # Only detect cars (class 2 in COCO dataset)

        logger.info("YOLOv5 model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Error loading YOLOv5 model: {e}")
        return None

# Initialize EasyOCR reader
def init_ocr_reader():
    try:
        # Initialize EasyOCR with English language
        reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
        logger.info("EasyOCR initialized successfully")
        return reader
    except Exception as e:
        logger.error(f"Error initializing EasyOCR: {e}")
        return None

# Global variables for models
yolo_model = load_model()
ocr_reader = init_ocr_reader()

# Function to preprocess image for license plate detection
def preprocess_image(image):
    # Resize image if too large
    max_dimension = 1280
    height, width = image.shape[:2]

    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        image = cv2.resize(image, (int(width * scale), int(height * scale)))

    return image

# Function to detect vehicles and extract license plate regions
def detect_vehicles(image, model):
    # Run inference with YOLOv5
    results = model(image)

    # Get vehicle detections
    vehicles = results.xyxy[0].cpu().numpy()  # xyxy format: [x1, y1, x2, y2, confidence, class]

    # Filter for vehicles (cars, trucks, motorcycles)
    vehicle_classes = [2, 7, 3]  # COCO classes for car, truck, motorcycle
    vehicles = [v for v in vehicles if int(v[5]) in vehicle_classes]

    return vehicles

# Function to extract potential license plate regions from vehicle
def extract_license_plate_regions(image, vehicle_boxes):
    plate_regions = []

    for box in vehicle_boxes:
        x1, y1, x2, y2 = map(int, box[:4])

        # Extract vehicle region with some margin
        margin = 10
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(image.shape[1], x2 + margin)
        y2 = min(image.shape[0], y2 + margin)

        vehicle_region = image[y1:y2, x1:x2]

        # Apply license plate detection heuristics
        # For simplicity, we'll use the bottom half of the vehicle as a potential plate region
        height, width = vehicle_region.shape[:2]
        plate_y1 = height // 2
        plate_region = vehicle_region[plate_y1:, :]

        plate_regions.append(plate_region)

    return plate_regions

# Function to enhance license plate image for better OCR
def enhance_plate_image(plate_image):
    # Convert to grayscale
    gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter to reduce noise while preserving edges
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY_INV, 11, 2)

    # Morphological operations to remove small noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return cleaned

# Function to recognize text from license plate image
def recognize_license_plate(plate_image, reader):
    # Recognize text using EasyOCR
    results = reader.readtext(plate_image)

    # Extract text and confidence
    texts = []
    for (bbox, text, prob) in results:
        texts.append((text, prob))

    return texts

# Function to post-process OCR results
def post_process_plate_text(texts):
    if not texts:
        return None, 0.0

    # Sort by confidence
    texts.sort(key=lambda x: x[1], reverse=True)

    # Get the highest confidence text
    best_text, best_conf = texts[0]

    # Clean the text (remove spaces, special characters)
    cleaned_text = re.sub(r'[^A-Z0-9]', '', best_text.upper())

    # If the cleaned text is too short, it's probably not a valid plate
    if len(cleaned_text) < 4 or len(cleaned_text) > 10:
        return None, 0.0

    return cleaned_text, best_conf

# Main function to process image and detect license plate
def process_image_for_license_plate(image_data):
    try:
        # Decode base64 image
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            # Extract the base64 part
            image_data = image_data.split(',')[1]

        # Convert base64 to image
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return {"success": False, "message": "Failed to decode image"}

        # Preprocess image
        processed_image = preprocess_image(image)

        # Detect vehicles
        vehicle_boxes = detect_vehicles(processed_image, yolo_model)

        if len(vehicle_boxes) == 0:
            return {"success": False, "message": "No vehicles detected in the image"}

        # Extract potential license plate regions
        plate_regions = extract_license_plate_regions(processed_image, vehicle_boxes)

        best_plate_text = None
        best_confidence = 0.0

        # Process each potential plate region
        for plate_region in plate_regions:
            # Enhance plate image
            enhanced_plate = enhance_plate_image(plate_region)

            # Recognize text
            texts = recognize_license_plate(enhanced_plate, ocr_reader)

            # Post-process text
            plate_text, confidence = post_process_plate_text(texts)

            if plate_text and confidence > best_confidence:
                best_plate_text = plate_text
                best_confidence = confidence

        if best_plate_text:
            return {
                "success": True,
                "plateNumber": best_plate_text,
                "confidence": float(best_confidence)
            }
        else:
            return {"success": False, "message": "No license plate detected"}

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return {"success": False, "message": f"Error processing image: {str(e)}"}

# API endpoint for license plate scanning
@app.route('/scan', methods=['POST'])
def scan_license_plate():
    try:
        # Get image data from request
        data = request.json
        if not data or 'image' not in data:
            return jsonify({"success": False, "message": "No image data provided"})

        image_data = data['image']

        # Process image
        start_time = time.time()
        result = process_image_for_license_plate(image_data)
        processing_time = time.time() - start_time

        logger.info(f"Processing completed in {processing_time:.2f} seconds")

        # Add processing time to result
        result['processingTime'] = f"{processing_time:.2f}s"

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in scan endpoint: {e}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"})

# Main entry point
if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 5002))

    # Check if models loaded successfully
    if yolo_model is None or ocr_reader is None:
        logger.error("Failed to load models. Exiting.")
        exit(1)

    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
