#!/usr/bin/env python3
"""
Test script for the advanced OCR service
"""

import os
import sys
import time
import argparse
import requests
import json
import base64
import cv2
import numpy as np
from PIL import Image
import io

def parse_arguments():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description='Test the advanced OCR service')
    
    parser.add_argument('--image', type=str, required=True,
                        help='Path to the image file')
    
    parser.add_argument('--url', type=str, default='http://localhost:5004',
                        help='URL of the OCR service (default: http://localhost:5004)')
    
    parser.add_argument('--feedback', type=str,
                        help='Provide feedback for the OCR result')
    
    parser.add_argument('--stats', action='store_true',
                        help='Get OCR accuracy stats')
    
    parser.add_argument('--performance', action='store_true',
                        help='Get OCR performance stats')
    
    return parser.parse_args()

def scan_license_plate(image_path, url):
    """
    Scan a license plate image using the OCR service
    
    Args:
        image_path: Path to the image file
        url: URL of the OCR service
        
    Returns:
        OCR result
    """
    # Check if the image file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found")
        return None
    
    # Read the image file
    with open(image_path, "rb") as image_file:
        # Encode the image as base64
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    
    # Add the data URL prefix
    base64_image = f"data:image/jpeg;base64,{encoded_string}"
    
    # Create the request payload
    payload = {
        "image": base64_image
    }
    
    # Send the request to the OCR service
    try:
        print(f"Sending request to {url}/scan...")
        start_time = time.time()
        response = requests.post(f"{url}/scan", json=payload)
        request_time = time.time() - start_time
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            
            # Print the result
            print(f"Request completed in {request_time:.2f} seconds")
            print("OCR Service Response:")
            print(json.dumps(result, indent=2))
            
            # Check if the request was successful
            if result.get("success"):
                print(f"\nLicense Plate: {result.get('plateNumber')}")
                print(f"Confidence: {result.get('confidence')}")
                print(f"Processing Time: {result.get('processingTime')}")
                print(f"Valid: {result.get('isValid')}")
                
                # Print all results if available
                if "allResults" in result:
                    print("\nAll Results:")
                    for i, res in enumerate(result["allResults"]):
                        print(f"  {i+1}. {res['text']} (confidence: {res['confidence']:.2f})")
                
                # Return the feedback ID if available
                return result.get("feedbackId"), result.get("plateNumber")
            else:
                print(f"\nError: {result.get('message')}")
                return None, None
        else:
            print(f"Error: HTTP {response.status_code} - {response.text}")
            return None, None
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None

def provide_feedback(feedback_id, corrected_text, url):
    """
    Provide feedback for an OCR result
    
    Args:
        feedback_id: Feedback ID
        corrected_text: Corrected text
        url: URL of the OCR service
        
    Returns:
        True if successful, False otherwise
    """
    # Create the request payload
    payload = {
        "feedbackId": feedback_id,
        "correctedText": corrected_text
    }
    
    # Send the request to the OCR service
    try:
        print(f"Sending feedback to {url}/feedback...")
        response = requests.post(f"{url}/feedback", json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            
            # Print the result
            print("Feedback Response:")
            print(json.dumps(result, indent=2))
            
            # Check if the request was successful
            if result.get("success"):
                print("\nFeedback recorded successfully")
                
                # Print stats if available
                if "stats" in result:
                    print("\nOCR Accuracy Stats:")
                    print(f"  Total Entries: {result['stats'].get('total_entries')}")
                    print(f"  Correct Entries: {result['stats'].get('correct_entries')}")
                    print(f"  Accuracy: {result['stats'].get('accuracy') * 100:.2f}%")
                    print(f"  Average Confidence: {result['stats'].get('average_confidence') * 100:.2f}%")
                
                return True
            else:
                print(f"\nError: {result.get('message')}")
                return False
        else:
            print(f"Error: HTTP {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def get_stats(url):
    """
    Get OCR accuracy stats
    
    Args:
        url: URL of the OCR service
        
    Returns:
        True if successful, False otherwise
    """
    # Send the request to the OCR service
    try:
        print(f"Getting stats from {url}/stats...")
        response = requests.get(f"{url}/stats")
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            
            # Print the result
            print("Stats Response:")
            print(json.dumps(result, indent=2))
            
            # Check if the request was successful
            if result.get("success"):
                # Print stats if available
                if "stats" in result:
                    print("\nOCR Accuracy Stats:")
                    print(f"  Total Entries: {result['stats'].get('total_entries')}")
                    print(f"  Correct Entries: {result['stats'].get('correct_entries')}")
                    print(f"  Accuracy: {result['stats'].get('accuracy') * 100:.2f}%")
                    print(f"  Average Confidence: {result['stats'].get('average_confidence') * 100:.2f}%")
                
                return True
            else:
                print(f"\nError: {result.get('message')}")
                return False
        else:
            print(f"Error: HTTP {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def get_performance(url):
    """
    Get OCR performance stats
    
    Args:
        url: URL of the OCR service
        
    Returns:
        True if successful, False otherwise
    """
    # Send the request to the OCR service
    try:
        print(f"Getting performance stats from {url}/performance...")
        response = requests.get(f"{url}/performance")
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            
            # Print the result
            print("Performance Response:")
            print(json.dumps(result, indent=2))
            
            # Check if the request was successful
            if result.get("success"):
                # Print stats if available
                if "stats" in result:
                    print("\nOCR Performance Stats:")
                    print(f"  Cache Hits: {result['stats'].get('cache_hits')}")
                    print(f"  Cache Misses: {result['stats'].get('cache_misses')}")
                    print(f"  Cache Hit Rate: {result['stats'].get('cache_hit_rate') * 100:.2f}%")
                    print(f"  Total Images Processed: {result['stats'].get('total_images_processed')}")
                    print(f"  Average Processing Time: {result['stats'].get('average_processing_time'):.2f} seconds")
                    print(f"  Parallel Tasks Executed: {result['stats'].get('parallel_tasks_executed')}")
                    print(f"  Image Cache Size: {result['stats'].get('image_cache_size')}")
                
                return True
            else:
                print(f"\nError: {result.get('message')}")
                return False
        else:
            print(f"Error: HTTP {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """
    Main entry point
    """
    # Parse arguments
    args = parse_arguments()
    
    # Get the base URL
    base_url = args.url.rstrip('/')
    
    # Check if we need to get stats
    if args.stats:
        get_stats(base_url)
        return 0
    
    # Check if we need to get performance stats
    if args.performance:
        get_performance(base_url)
        return 0
    
    # Check if we need to provide feedback
    if args.feedback:
        # We need both the feedback ID and the corrected text
        if ':' not in args.feedback:
            print("Error: Feedback must be in the format 'feedback_id:corrected_text'")
            return 1
        
        # Split the feedback
        feedback_id, corrected_text = args.feedback.split(':', 1)
        
        # Provide feedback
        provide_feedback(feedback_id, corrected_text, base_url)
        return 0
    
    # Scan the license plate
    feedback_id, plate_number = scan_license_plate(args.image, base_url)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
