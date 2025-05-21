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

# Function to apply multiple preprocessing techniques to improve OCR
def apply_multiple_preprocessings(image):
    """
    Apply multiple preprocessing techniques to the same image

    Args:
        image: Original image

    Returns:
        List of preprocessed images
    """
    preprocessed_images = []

    # Original grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    preprocessed_images.append(("original_gray", gray))

    # Resize to larger dimensions for better OCR
    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    preprocessed_images.append(("resized", resized))

    # Apply bilateral filter to remove noise while keeping edges sharp
    bilateral = cv2.bilateralFilter(gray, 11, 17, 17)
    preprocessed_images.append(("bilateral", bilateral))

    # Apply adaptive threshold
    thresh = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 11, 2)
    preprocessed_images.append(("adaptive_threshold", thresh))

    # Apply Otsu's thresholding
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    preprocessed_images.append(("otsu", otsu))

    # Apply histogram equalization
    hist_eq = cv2.equalizeHist(gray)
    preprocessed_images.append(("hist_eq", hist_eq))

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    clahe_img = clahe.apply(gray)
    preprocessed_images.append(("clahe", clahe_img))

    # Apply morphological operations
    kernel = np.ones((1, 1), np.uint8)
    erosion = cv2.erode(gray, kernel, iterations=1)
    dilation = cv2.dilate(gray, kernel, iterations=1)
    opening = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

    preprocessed_images.append(("erosion", erosion))
    preprocessed_images.append(("dilation", dilation))
    preprocessed_images.append(("opening", opening))
    preprocessed_images.append(("closing", closing))

    return preprocessed_images

# Function to detect license plate regions in an image
def detect_license_plate_regions(image):
    """
    Detect potential license plate regions in an image

    Args:
        image: Original image

    Returns:
        List of potential license plate regions
    """
    regions = []

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
        # If no contours found, add the full image as a fallback
        regions.append(("full_image", gray))
        return regions

    # Sort contours by area and keep the largest ones
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15]

    # Find potential license plate contours
    for i, c in enumerate(contours):
        # Get the bounding rectangle
        x, y, w, h = cv2.boundingRect(c)

        # Calculate aspect ratio
        aspect_ratio = float(w) / h

        # License plates typically have an aspect ratio between 1.5 and 5
        if 1.5 <= aspect_ratio <= 5 and w > 60 and h > 20:
            # Crop the region
            plate_region = gray[max(0, y-5):min(gray.shape[0], y+h+5), max(0, x-5):min(gray.shape[1], x+w+5)]

            if plate_region.size > 0:
                # Resize for better OCR
                plate_region = cv2.resize(plate_region, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

                # Apply threshold
                _, plate_region_thresh = cv2.threshold(plate_region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                regions.append((f"contour_{i}", plate_region))
                regions.append((f"contour_{i}_thresh", plate_region_thresh))

    # If no suitable contours found, add the full image as a fallback
    if not regions:
        regions.append(("full_image", gray))

    return regions

# Function to recognize text from multiple images
def recognize_text_from_multiple_images(images):
    """
    Try to recognize text from multiple preprocessed images

    Args:
        images: List of (name, image) tuples

    Returns:
        List of (text, confidence, source) tuples
    """
    results = []

    # Different PSM modes to try
    psm_modes = [7, 8, 6, 3]

    for name, img in images:
        for psm in psm_modes:
            # Configure Tesseract with different PSM modes
            custom_config = f'--oem 3 --psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

            try:
                # Get OCR result
                text = pytesseract.image_to_string(img, config=custom_config)

                # Clean the text
                text = ''.join(e for e in text if e.isalnum())

                if text and len(text) >= 4:  # Most license plates have at least 4 characters
                    # Get confidence
                    data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)

                    # Calculate average confidence for all detected text
                    confidences = [int(conf) for conf in data['conf'] if conf != '-1']
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

                    results.append((text, avg_confidence / 100.0, f"{name}_psm{psm}"))

            except Exception as e:
                print(f"Error in OCR for {name} with PSM {psm}: {str(e)}")

    # Sort results by confidence
    results.sort(key=lambda x: x[1], reverse=True)

    return results

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

# Function to validate license plate format
def is_valid_license_plate(text, region='in'):
    """
    Check if the text matches a valid license plate format

    Args:
        text: License plate text
        region: Region code (in for India, us for USA, etc.)

    Returns:
        Boolean indicating if the text is a valid license plate
    """
    if not text or len(text) < 4:
        return False

    # For Indian plates
    if region == 'in':
        # Basic pattern: 2 letters + 1-2 digits + 1-3 letters + 1-4 digits
        pattern = r'^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{1,4}$'
        return bool(re.match(pattern, text))

    # For other regions, just check if it has a mix of letters and numbers
    letters = sum(1 for c in text if c.isalpha())
    digits = sum(1 for c in text if c.isdigit())

    return letters > 0 and digits > 0 and 4 <= len(text) <= 10

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

            # Start timing
            start_time = time.time()

            # Apply multiple preprocessing techniques
            print("Applying multiple preprocessing techniques...")
            preprocessed_images = apply_multiple_preprocessings(image_cv)

            # Detect potential license plate regions
            print("Detecting license plate regions...")
            plate_regions = detect_license_plate_regions(image_cv)

            # Combine all images for OCR
            all_images = preprocessed_images + plate_regions

            # Recognize text from all images
            print("Performing OCR on all preprocessed images...")
            ocr_results = recognize_text_from_multiple_images(all_images)

            # Calculate processing time
            processing_time = time.time() - start_time

            # If no results found
            if not ocr_results:
                print("No license plate text detected in any of the processed images")
                return jsonify({"success": False, "message": "No license plate text detected in the image"})

            # Get the top 3 results
            top_results = ocr_results[:3]

            # Log the top results
            for i, (text, confidence, source) in enumerate(top_results):
                print(f"Result {i+1}: '{text}' (confidence: {confidence:.2f}, source: {source})")

            # Get the best result
            best_text, best_confidence, best_source = top_results[0]

            # Format the plate text
            formatted_plate = format_license_plate(best_text, region='in')

            # Validate the plate format
            is_valid = is_valid_license_plate(formatted_plate, region='in')

            print(f"Best license plate detected: {formatted_plate} (valid: {is_valid}) with confidence {best_confidence:.2f} from {best_source}")

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
                        "confidence": best_confidence,
                        "processingTime": f"{processing_time:.2f}s",
                        "vehicle": vehicle_dict,
                        "activeTicket": ticket_dict,
                        "dataSource": "mongodb",
                        "isValid": is_valid
                    })

            # Return just the plate if not in database
            return jsonify({
                "success": True,
                "plateNumber": formatted_plate,
                "confidence": best_confidence,
                "processingTime": f"{processing_time:.2f}s",
                "isValid": is_valid,
                "allResults": [{"text": text, "confidence": conf} for text, conf, _ in top_results[:3]]
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

    print(f"Starting Enhanced License Plate OCR service on port {port}")
    print("This service uses multiple preprocessing techniques and OCR approaches")
    print("Optimized for Indian license plates")

    app.run(host='0.0.0.0', port=port, debug=False)
