import requests
import json
import base64
import os
import sys

def test_ocr_service(image_path=None):
    """
    Test the OCR service by sending a request with an image

    Args:
        image_path: Path to an image file to test with
    """
    # OCR service URL
    url = "http://localhost:5004/scan"

    # If no image path provided, create a simple test payload
    if not image_path:
        print("No image path provided. Sending a test request with a dummy image.")
        # Create a minimal base64 image (1x1 pixel)
        minimal_base64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAIBAQIBAQICAgICAgICAwUDAwMDAwYEBAMFBwYHBwcGBwcICQsJCAgKCAcHCg0KCgsMDAwMBwkODw0MDgsMDAz/2wBDAQICAgMDAwYDAwYMCAcIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAz/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9/KKKKAP/2Q=="

        # Prepare the request payload
        payload = {
            "image": minimal_base64
        }

        try:
            print(f"Sending test request to http://localhost:5004/scan")
            response = requests.post("http://localhost:5004/scan", json=payload)

            print(f"Response status code: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print("\nResponse:")
                print(json.dumps(result, indent=2))

                if result.get("success"):
                    print("\nOCR service is working!")
                else:
                    print(f"\nOCR service returned an error: {result.get('message')}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error sending request: {str(e)}")

        return

    # Check if the image file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return

    # Read the image file and convert to base64
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    # Add data URL prefix
    base64_image = f"data:image/jpeg;base64,{encoded_string}"

    # Prepare the request payload
    payload = {
        "image": base64_image
    }

    # Send the request
    try:
        print(f"Sending request to {url} with image: {image_path}")
        response = requests.post(url, json=payload)

        # Check the response
        if response.status_code == 200:
            result = response.json()
            print("\nOCR Result:")
            print(json.dumps(result, indent=2))

            if result.get("success"):
                print(f"\nDetected license plate: {result.get('plateNumber')}")
                print(f"Confidence: {result.get('confidence')}")
                print(f"Processing time: {result.get('processingTime')}")

                if "vehicle" in result:
                    print("\nVehicle details:")
                    print(json.dumps(result.get("vehicle"), indent=2))

                if "activeTicket" in result and result.get("activeTicket"):
                    print("\nActive ticket details:")
                    print(json.dumps(result.get("activeTicket"), indent=2))
            else:
                print(f"Error: {result.get('message')}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error sending request: {str(e)}")

if __name__ == "__main__":
    # Check if an image path was provided as a command-line argument
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        test_ocr_service(image_path)
    else:
        # No image path provided, just test if the service is running
        test_ocr_service()
