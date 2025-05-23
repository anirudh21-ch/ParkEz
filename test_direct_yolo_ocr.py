#!/usr/bin/env python3
"""
Test script for the direct YOLO-based license plate OCR
This script tests the OCR with real images from the test_images directory
"""

import os
import sys
import requests
import json
import base64
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_direct_yolo_ocr')

# OCR API configuration
OCR_API_URL = "http://192.168.1.6:5005/scan"

def test_image(image_path):
    """
    Test OCR with a real image file

    Args:
        image_path: Path to the image file

    Returns:
        OCR response JSON
    """
    try:
        logger.info(f"Testing OCR with image: {image_path}")

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
        logger.error(f"Error in test_image: {str(e)}")
        return None

def main():
    # Check if test images directory exists
    test_images_dir = "./test_images"
    if not os.path.exists(test_images_dir):
        logger.error(f"Test images directory not found: {test_images_dir}")
        return 1

    # Get list of image files
    image_files = [f for f in os.listdir(test_images_dir)
                  if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    if not image_files:
        logger.error(f"No image files found in {test_images_dir}")
        return 1

    logger.info(f"Found {len(image_files)} test images")

    # Test each image
    success_count = 0
    for image_file in image_files:
        image_path = os.path.join(test_images_dir, image_file)
        logger.info(f"\n\n===== Testing image: {image_file} =====")

        result = test_image(image_path)

        if result and result.get('success', False):
            plate_number = result.get('plateNumber', 'Unknown')
            confidence = result.get('confidence', 0)

            # Get all detected plates
            all_results = result.get('allResults', [])
            all_plates = [r.get('text', '') for r in all_results]

            logger.info(f"SUCCESS: Detected license plate: {plate_number} with confidence {confidence:.2f}")
            logger.info(f"All detected plates: {all_plates}")
            success_count += 1
        else:
            logger.error(f"FAILED: Could not detect license plate in {image_file}")

        # Wait a bit between tests
        time.sleep(1)

    # Summary
    logger.info(f"\n\n===== Test Summary =====")
    logger.info(f"Total images tested: {len(image_files)}")
    logger.info(f"Successful detections: {success_count}")
    logger.info(f"Failed detections: {len(image_files) - success_count}")
    logger.info(f"Success rate: {success_count / len(image_files) * 100:.2f}%")

    return 0

if __name__ == "__main__":
    sys.exit(main())
