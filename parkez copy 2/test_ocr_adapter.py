#!/usr/bin/env python3
"""
Test script for the OCR adapter
"""

import requests
import base64
import json
import sys
import os

def test_ocr_adapter(image_path, api_url, operation="entry"):
    """
    Test the OCR adapter with a sample image
    """
    print(f"Testing OCR adapter at {api_url} with image {image_path}")
    
    # Check if the image file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file {image_path} does not exist")
        return
    
    # Read the image file
    with open(image_path, "rb") as image_file:
        # Convert the image to base64
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        
        # Add the base64 prefix
        base64_image = f"data:image/jpeg;base64,{encoded_string}"
        
        # Create the request payload
        payload = {
            "image": base64_image,
            "operation": operation
        }
        
        # If it's an entry operation, add zone and slot info
        if operation == "entry":
            payload["zoneId"] = "6462d5ab9d2b1e5a4f3a1234"  # Example zone ID
            payload["slotNumber"] = "A1"  # Example slot number
        
        # Print the request details
        print(f"Sending request to {api_url}")
        print(f"Operation: {operation}")
        print(f"Image size: {len(base64_image)} bytes")
        
        try:
            # Send the request to the OCR adapter
            response = requests.post(
                api_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=30
            )
            
            # Print the response
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text}")
            
            # Parse the JSON response
            if response.status_code == 200:
                try:
                    result = response.json()
                    print("\nParsed response:")
                    print(f"Success: {result.get('success', False)}")
                    print(f"Plate number: {result.get('plateNumber', 'N/A')}")
                    print(f"Confidence: {result.get('confidence', 0)}")
                    print(f"Message: {result.get('message', 'N/A')}")
                except json.JSONDecodeError:
                    print("Error: Could not parse JSON response")
            
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Check if the correct number of arguments is provided
    if len(sys.argv) < 3:
        print("Usage: python test_ocr_adapter.py <image_path> <api_url> [operation]")
        print("Example: python test_ocr_adapter.py ./test_images/car1.jpg http://192.168.1.6:5005/scan entry")
        sys.exit(1)
    
    # Get the arguments
    image_path = sys.argv[1]
    api_url = sys.argv[2]
    operation = sys.argv[3] if len(sys.argv) > 3 else "entry"
    
    # Test the OCR adapter
    test_ocr_adapter(image_path, api_url, operation)
