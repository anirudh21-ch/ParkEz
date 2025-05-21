import cv2
import numpy as np
import os

def create_license_plate_image(text="ABC123", output_path="test_license_plate.jpg"):
    """
    Create a simple license plate image with the given text
    
    Args:
        text: The license plate text
        output_path: Path to save the image
    """
    # Create a white image (license plate background)
    img = np.ones((200, 400, 3), np.uint8) * 255
    
    # Add a black border
    cv2.rectangle(img, (10, 10), (390, 190), (0, 0, 0), 2)
    
    # Add the license plate text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, text, (100, 100), font, 2, (0, 0, 0), 4, cv2.LINE_AA)
    
    # Save the image
    cv2.imwrite(output_path, img)
    print(f"Created test license plate image at {output_path}")
    
    return output_path

if __name__ == "__main__":
    # Create a directory for test images if it doesn't exist
    os.makedirs("test_images", exist_ok=True)
    
    # Create a few test license plates
    create_license_plate_image("ABC123", "test_images/plate1.jpg")
    create_license_plate_image("XYZ789", "test_images/plate2.jpg")
    create_license_plate_image("DEF456", "test_images/plate3.jpg")
