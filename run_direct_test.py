#!/usr/bin/env python3
"""
Direct test script that uses the NumberPlate-Detection-Extraction code directly
"""

import os
import sys
import logging
import cv2
import numpy as np
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('run_direct_test')

# Add the NumberPlate-Detection-Extraction directory to the path
sys.path.append('./NumberPlate-Detection-Extraction')

# Import the object_detection function from deeplearning.py
try:
    from deeplearning import object_detection
    logger.info("Successfully imported object_detection from deeplearning.py")
except ImportError as e:
    logger.error(f"Failed to import object_detection: {str(e)}")
    sys.exit(1)

def test_image(image_path):
    """
    Test OCR with a real image file using the direct object_detection function
    
    Args:
        image_path: Path to the image file
        
    Returns:
        List of detected license plate texts
    """
    try:
        logger.info(f"Testing OCR with image: {image_path}")
        
        # Check if file exists
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        # Generate a unique filename for the result
        filename = os.path.basename(image_path)
        
        # Call the object_detection function directly
        start_time = time.time()
        text_list = object_detection(image_path, filename)
        processing_time = time.time() - start_time
        
        logger.info(f"Processing time: {processing_time:.2f}s")
        logger.info(f"Detected license plates: {text_list}")
        
        # Check the result image
        result_path = os.path.join('./NumberPlate-Detection-Extraction/static/predict', filename)
        if os.path.exists(result_path):
            logger.info(f"Result image saved to: {result_path}")
        
        return text_list
        
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
        
        text_list = test_image(image_path)
        
        if text_list and len(text_list) > 0:
            logger.info(f"SUCCESS: Detected license plates: {text_list}")
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
