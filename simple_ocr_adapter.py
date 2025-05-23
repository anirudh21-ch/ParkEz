from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import random
import logging
import base64
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('simple_ocr_adapter')

app = Flask(__name__)
CORS(app)

# Sample license plates
SAMPLE_PLATES = [
    "MH12DE1234",
    "KA01AB1234",
    "DL01AB1234",
    "TN01AB1234",
    "UP01AB1234"
]

def format_license_plate(plate_text, region='in'):
    """Format the license plate text based on region."""
    # For Indian plates, ensure proper format
    if region == 'in':
        # Remove spaces and convert to uppercase
        plate_text = plate_text.replace(' ', '').upper()

        # Basic validation for Indian plates (2 letters, 2 digits, 2 letters, 4 digits)
        import re
        if not re.match(r'^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{1,4}$', plate_text):
            # If not in expected format, try to fix it
            # Extract letters and numbers
            letters = ''.join(re.findall(r'[A-Z]', plate_text))
            numbers = ''.join(re.findall(r'\d', plate_text))

            # If we have enough characters, reconstruct in proper format
            if len(letters) >= 4 and len(numbers) >= 6:
                plate_text = f"{letters[:2]}{numbers[:2]}{letters[2:4]}{numbers[2:6]}"
            elif len(letters) >= 2 and len(numbers) >= 6:
                plate_text = f"{letters[:2]}{numbers[:2]}AB{numbers[2:6]}"
            else:
                # Not enough characters, return a sample plate
                plate_text = random.choice(SAMPLE_PLATES)

    return plate_text

@app.route('/scan', methods=['POST'])
def scan():
    """Endpoint to scan license plates from images."""
    try:
        # Get the request data
        data = request.json

        # Log the request
        logger.info("Received OCR scan request")

        # Check if image data is provided
        if 'image' not in data:
            logger.error("No image data in request")
            return jsonify({
                "success": False,
                "message": "No image data provided"
            })

        # Check if image data is valid
        image_data = data['image']
        if not image_data:
            logger.error("Empty image data")
            return jsonify({
                "success": False,
                "message": "Empty image data provided"
            })

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
            return jsonify({
                "success": False,
                "message": "Invalid image format"
            })

        # Decode base64 to image (we don't actually process the image in this simple adapter)
        try:
            # Just decode to verify it's valid base64
            image_bytes = base64.b64decode(image_data)

            # Save to temporary file (just to simulate processing)
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
                temp_path = temp.name
                temp.write(image_bytes)

            # Get the operation type (entry or exit)
            operation = data.get('operation', 'entry')

            # Generate a license plate for testing
            if operation == 'entry':
                plate_text = random.choice(SAMPLE_PLATES)
            else:
                # For exit, use a consistent plate that's likely to be in the database
                plate_text = "MH12DE1234"

            # Format the plate text
            formatted_plate = format_license_plate(plate_text, region='in')
            logger.info(f"Using fallback license plate: {formatted_plate}")

            # Clean up temporary file
            os.unlink(temp_path)

            # Add feedback ID for potential corrections
            feedback_id = f"{int(time.time())}_{formatted_plate}"

            # Return the result
            return jsonify({
                "success": True,
                "plateNumber": formatted_plate,
                "confidence": 0.95,  # Using a fixed high confidence
                "processingTime": "0.5s",
                "operation": operation,
                "feedbackId": feedback_id,
                "isValid": True,
                "fallbackMode": True,
                "message": "Using fallback mode"
            })

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"Error processing image: {str(e)}"
            })

    except Exception as e:
        logger.error(f"Error in scan endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error processing request: {str(e)}"
        })

if __name__ == '__main__':
    port = 5005
    logger.info(f"Starting Simple OCR Adapter service on port {port}")
    logger.info(f"Server running at http://192.168.31.33:{port}/")
    logger.info(f"For local access: http://localhost:{port}/")
    logger.info(f"For network access: http://192.168.31.33:{port}/")
    app.run(host='192.168.31.33', port=port)
