#!/usr/bin/env python3
"""
Test script for the YOLO-based license plate OCR service
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
logger = logging.getLogger('test_yolo_ocr')

# OCR API configuration
OCR_API_URL = "http://192.168.1.6:5005/scan"
FEEDBACK_API_URL = "http://192.168.1.6:5005/feedback"

def create_test_image(license_plate_text="21 BH 2345 AA"):
    """
    Create a test image with the specified license plate text

    Args:
        license_plate_text: Text to display on the license plate

    Returns:
        PIL Image object
    """
    try:
        # Create a blank image with white background
        width, height = 800, 600
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)

        # Try to load a font
        try:
            font = ImageFont.truetype("Arial.ttf", 36)
        except IOError:
            # Fallback to default font
            font = ImageFont.load_default()

        # Draw a license plate
        plate_width, plate_height = 400, 100
        plate_x = (width - plate_width) // 2
        plate_y = (height - plate_height) // 2

        # Draw plate background
        draw.rectangle(
            [(plate_x, plate_y), (plate_x + plate_width, plate_y + plate_height)],
            fill='yellow',
            outline='black',
            width=2
        )

        # Draw text
        text_width = draw.textlength(license_plate_text, font=font)
        text_x = plate_x + (plate_width - text_width) // 2
        text_y = plate_y + (plate_height - 36) // 2
        draw.text((text_x, text_y), license_plate_text, fill='black', font=font)

        # Draw a car outline around the plate
        car_width, car_height = 600, 300
        car_x = (width - car_width) // 2
        car_y = (height - car_height) // 2

        # Simple car outline
        draw.rectangle(
            [(car_x, car_y), (car_x + car_width, car_y + car_height)],
            outline='gray',
            width=1
        )

        return image

    except Exception as e:
        logger.error(f"Error creating test image: {str(e)}")
        return None

def image_to_base64(image):
    """
    Convert PIL Image to base64 string

    Args:
        image: PIL Image object

    Returns:
        Base64 encoded string
    """
    try:
        # Convert to JPEG
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Add data URL prefix
        return f"data:image/jpeg;base64,{img_str}"

    except Exception as e:
        logger.error(f"Error converting image to base64: {str(e)}")
        return None

def test_entry_scan(license_plate="21 BH 2345 AA"):
    """
    Test the entry scan functionality

    Args:
        license_plate: License plate text to use in the test

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
        logger.info(f"Response: {json.dumps(result, indent=2)}")

        # Check if successful
        if not result.get('success', False):
            logger.error(f"API request failed: {result.get('message', 'Unknown error')}")
            return None

        return result

    except Exception as e:
        logger.error(f"Error in test_entry_scan: {str(e)}")
        return None

def test_exit_scan(license_plate="21 BH 2345 AA"):
    """
    Test the exit scan functionality

    Args:
        license_plate: License plate text to use in the test

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
        logger.info(f"Response: {json.dumps(result, indent=2)}")

        # Check if successful
        if not result.get('success', False):
            logger.error(f"API request failed: {result.get('message', 'Unknown error')}")
            return None

        return result

    except Exception as e:
        logger.error(f"Error in test_exit_scan: {str(e)}")
        return None

def test_feedback(feedback_id, corrected_text):
    """
    Test the feedback functionality

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
        logger.info(f"Response: {json.dumps(result, indent=2)}")

        # Check if successful
        if not result.get('success', False):
            logger.error(f"API request failed: {result.get('message', 'Unknown error')}")
            return None

        return result

    except Exception as e:
        logger.error(f"Error in test_feedback: {str(e)}")
        return None

def test_real_image(image_path):
    """
    Test the OCR with a real image file

    Args:
        image_path: Path to the image file

    Returns:
        OCR response JSON
    """
    try:
        logger.info(f"Testing OCR with real image: {image_path}")

        # Check if file exists
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None

        # Read the image
        with open(image_path, 'rb') as f:
            image_data = f.read()

        # Convert to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        base64_image = f"data:image/jpeg;base64,{base64_image}"

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
        logger.info(f"Response: {json.dumps(result, indent=2)}")

        # Check if successful
        if not result.get('success', False):
            logger.error(f"API request failed: {result.get('message', 'Unknown error')}")
            return None

        return result

    except Exception as e:
        logger.error(f"Error in test_real_image: {str(e)}")
        return None

def main():
    # Check if test images directory exists
    test_images_dir = "./test_images"
    if os.path.exists(test_images_dir):
        # Test with real images
        logger.info(f"Testing with real images from {test_images_dir}")
        image_files = [f for f in os.listdir(test_images_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]

        if not image_files:
            logger.warning(f"No image files found in {test_images_dir}")

        for image_file in image_files:
            image_path = os.path.join(test_images_dir, image_file)
            logger.info(f"Testing with image: {image_file}")
            result = test_real_image(image_path)

            if result:
                logger.info(f"Successfully detected license plate in {image_file}: {result.get('plateNumber', 'Unknown')}")
            else:
                logger.error(f"Failed to detect license plate in {image_file}")

            # Wait a bit between tests
            time.sleep(1)
    else:
        # Test with generated images
        logger.info("Test images directory not found, using generated test images")

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

    return 0

if __name__ == "__main__":
    sys.exit(main())
