import requests
import base64
import json
import sys
import os

def test_ocr_service(image_path, api_url="http://localhost:5006/scan", operation="entry", zone_id=None, slot_number=None):
    """
    Test the OCR service with a local image file

    Args:
        image_path: Path to the image file
        api_url: URL of the OCR service
        operation: Operation type (entry or exit)
        zone_id: Zone ID for entry operation
        slot_number: Slot number for entry operation
    """
    # Check if the image file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found")
        return

    # Read the image file
    with open(image_path, "rb") as image_file:
        # Encode the image as base64
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

    # Add the data URL prefix
    base64_image = f"data:image/jpeg;base64,{encoded_string}"

    # Create the request payload
    payload = {
        "image": base64_image,
        "operation": operation
    }

    # Add zone_id and slot_number for entry operation if provided
    if operation == "entry" and zone_id and slot_number:
        payload["zoneId"] = zone_id
        payload["slotNumber"] = slot_number

    # Send the request to the OCR service
    try:
        response = requests.post(api_url, json=payload)

        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()

            # Print the result
            print("OCR Service Response:")
            print(json.dumps(result, indent=2))

            # Check if the request was successful
            if result.get("success"):
                print(f"\nLicense Plate: {result.get('plateNumber')}")
                print(f"Confidence: {result.get('confidence')}")
                print(f"Processing Time: {result.get('processingTime')}")

                # Print ticket information if available
                if "ticketId" in result:
                    print(f"\nTicket created successfully!")
                    print(f"Ticket ID: {result.get('ticketId')}")
                    print(f"Message: {result.get('message')}")

                # Print checkout information if available
                if "amount" in result:
                    print(f"\nCheckout completed successfully!")
                    print(f"Entry Time: {result.get('entryTime')}")
                    print(f"Exit Time: {result.get('exitTime')}")
                    print(f"Duration: {result.get('duration')}")
                    print(f"Amount: ${result.get('amount')}")
                    print(f"Message: {result.get('message')}")

                # Print all results if available
                if "allResults" in result:
                    print("\nAll Results:")
                    for i, res in enumerate(result["allResults"]):
                        print(f"  {i+1}. {res['text']} (confidence: {res['confidence']:.2f})")
            else:
                print(f"\nError: {result.get('message')}")
        else:
            print(f"Error: HTTP {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Check if an image path was provided
    if len(sys.argv) < 2:
        print("Usage: python test_ocr_service.py <image_path> [api_url] [operation] [zone_id] [slot_number]")
        print("  operation: 'entry' or 'exit' (default: 'entry')")
        print("  zone_id: Zone ID for entry operation (required for entry)")
        print("  slot_number: Slot number for entry operation (required for entry)")
        sys.exit(1)

    # Get the image path from the command line arguments
    image_path = sys.argv[1]

    # Get the API URL from the command line arguments or use the default
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5006/scan"

    # Get the operation type from the command line arguments or use the default
    operation = sys.argv[3] if len(sys.argv) > 3 else "entry"

    # Get the zone_id and slot_number if provided
    zone_id = sys.argv[4] if len(sys.argv) > 4 else None
    slot_number = sys.argv[5] if len(sys.argv) > 5 else None

    # Test the OCR service
    test_ocr_service(image_path, api_url, operation, zone_id, slot_number)
