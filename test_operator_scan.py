#!/usr/bin/env python3
"""
Test script for the operator scanning interface
This script simulates the mobile app's interaction with the OCR service
"""

import os
import sys
import requests
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_operator_scan')

# OCR API configuration
OCR_API_URL = "http://192.168.1.6:5005/scan"
FEEDBACK_API_URL = "http://192.168.1.6:5005/feedback"

def create_test_image(license_plate_text="21 BH 2345 AA"):
    """
    Create a test image with the specified license plate text

    Returns:
        PIL Image object
    """
    try:
        # Create a blank image (white background)
        img = Image.new('RGB', (500, 200), color=(255, 255, 255))

        # Get a drawing context
        draw = ImageDraw.Draw(img)

        # Draw a black rectangle for the license plate
        draw.rectangle([(50, 50), (450, 150)], outline=(0, 0, 0), width=2)

        # Add text for the license plate number
        try:
            # Try to use a TrueType font if available
            font = ImageFont.truetype("Arial", 36)
        except IOError:
            # Fall back to default font
            font = ImageFont.load_default()

        # Calculate text position to center it
        text_width = draw.textlength(license_plate_text, font=font)
        text_position = ((500 - text_width) // 2, 90)

        # Draw the text
        draw.text(text_position, license_plate_text, fill=(0, 0, 0), font=font)

        logger.info(f"Test image created with license plate: {license_plate_text}")

        return img

    except Exception as e:
        logger.error(f"Error creating test image: {str(e)}")
        return None

def image_to_base64(image):
    """
    Convert a PIL Image to base64 string

    Args:
        image: PIL Image object

    Returns:
        Base64 encoded string with data URL prefix
    """
    try:
        # Convert to JPEG
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Add data URL prefix
        return f"data:image/jpeg;base64,{img_str}"

    except Exception as e:
        logger.error(f"Error converting image to base64: {str(e)}")
        return None

def test_entry_scan(license_plate="21 BH 2345 AA"):
    """
    Test the entry scan operation

    Args:
        license_plate: License plate text to use in the test image

    Returns:
        OCR response JSON
    """
    try:
        logger.info(f"Testing ENTRY scan for license plate: {license_plate}")

        # Create a test image
        image = create_test_image(license_plate)
        if image is None:
            return None

        # Convert to base64
        base64_image = image_to_base64(image)
        if base64_image is None:
            return None

        # Prepare request payload
        payload = {
            "image": base64_image,
            "operation": "entry"
        }

        # Send request to API
        logger.info(f"Sending request to {OCR_API_URL}")
        response = requests.post(OCR_API_URL, json=payload)

        # Check response
        if response.status_code != 200:
            logger.error(f"API request failed with status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None

        # Parse response
        result = response.json()

        if not result.get("success", False):
            logger.error(f"API returned error: {result.get('message', 'Unknown error')}")
            return None

        # Log result
        plate_number = result.get("plateNumber", "Unknown")
        confidence = result.get("confidence", 0)

        logger.info(f"API detected license plate: {plate_number} with confidence {confidence}")
        logger.info(f"Full API response: {json.dumps(result, indent=2)}")

        return result

    except Exception as e:
        logger.error(f"Error in test_entry_scan: {str(e)}")
        return None

def test_exit_scan(license_plate="21 BH 2345 AA"):
    """
    Test the exit scan operation

    Args:
        license_plate: License plate text to use in the test image

    Returns:
        OCR response JSON
    """
    try:
        logger.info(f"Testing EXIT scan for license plate: {license_plate}")

        # Create a test image
        image = create_test_image(license_plate)
        if image is None:
            return None

        # Convert to base64
        base64_image = image_to_base64(image)
        if base64_image is None:
            return None

        # Prepare request payload
        payload = {
            "image": base64_image,
            "operation": "exit"
        }

        # Send request to API
        logger.info(f"Sending request to {OCR_API_URL}")
        response = requests.post(OCR_API_URL, json=payload)

        # Check response
        if response.status_code != 200:
            logger.error(f"API request failed with status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None

        # Parse response
        result = response.json()

        if not result.get("success", False):
            logger.error(f"API returned error: {result.get('message', 'Unknown error')}")
            return None

        # Log result
        plate_number = result.get("plateNumber", "Unknown")
        confidence = result.get("confidence", 0)

        logger.info(f"API detected license plate: {plate_number} with confidence {confidence}")
        logger.info(f"Full API response: {json.dumps(result, indent=2)}")

        return result

    except Exception as e:
        logger.error(f"Error in test_exit_scan: {str(e)}")
        return None

def test_feedback(feedback_id, corrected_text="21 BH 2345 AA"):
    """
    Test the feedback endpoint

    Args:
        feedback_id: Feedback ID from the OCR response
        corrected_text: Corrected license plate text

    Returns:
        Feedback response JSON
    """
    try:
        logger.info(f"Testing feedback for ID: {feedback_id}")
        logger.info(f"Corrected text: {corrected_text}")

        # Prepare request payload
        payload = {
            "feedbackId": feedback_id,
            "correctedText": corrected_text
        }

        # Send request to API
        logger.info(f"Sending request to {FEEDBACK_API_URL}")
        response = requests.post(FEEDBACK_API_URL, json=payload)

        # Check response
        if response.status_code != 200:
            logger.error(f"API request failed with status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None

        # Parse response
        result = response.json()

        if not result.get("success", False):
            logger.error(f"API returned error: {result.get('message', 'Unknown error')}")
            return None

        # Log result
        logger.info(f"Feedback response: {json.dumps(result, indent=2)}")

        return result

    except Exception as e:
        logger.error(f"Error in test_feedback: {str(e)}")
        return None

def main():
    # Test entry scan
    entry_result = test_entry_scan()

    if entry_result:
        logger.info("Entry scan test completed successfully")

        # Test feedback if we have a feedback ID
        feedback_id = entry_result.get("feedbackId")
        if feedback_id:
            time.sleep(1)  # Wait a bit before sending feedback
            feedback_result = test_feedback(feedback_id, "MH 12 DE 1234")
            if feedback_result:
                logger.info("Feedback test completed successfully")

    # Wait a bit before the exit scan
    time.sleep(1)

    # Test exit scan
    exit_result = test_exit_scan()

    if exit_result:
        logger.info("Exit scan test completed successfully")

    # Overall result
    if entry_result and exit_result:
        logger.info("All tests completed successfully")
        return 0
    else:
        logger.error("Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
