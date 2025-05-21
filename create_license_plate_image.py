import cv2
import numpy as np
import os

def create_indian_license_plate(text="GJ03ER0563", output_path="ocr_feedback/images/indian_plate.jpg"):
    """
    Create an Indian license plate image with the given text

    Args:
        text: The license plate text
        output_path: Path to save the image
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Create a white image (license plate background)
    img = np.ones((200, 500, 3), np.uint8) * 255

    # Add a black border
    cv2.rectangle(img, (10, 10), (490, 190), (0, 0, 0), 2)

    # Add a blue background for the license plate (typical for Indian plates)
    cv2.rectangle(img, (15, 15), (485, 185), (255, 220, 0), -1)  # Light blue fill

    # Add the "IND" text in the left corner with a small box
    cv2.rectangle(img, (20, 20), (70, 50), (255, 255, 255), -1)  # White box for IND
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "IND", (25, 42), font, 0.7, (0, 0, 0), 2, cv2.LINE_AA)

    # Format the license plate text with proper spacing
    if len(text) >= 10:  # For format like GJ03ER0563
        part1 = text[:4]  # GJ03
        part2 = text[4:]  # ER0563

        # Add the license plate text with better spacing
        cv2.putText(img, part1, (100, 110), font, 1.5, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, part2, (230, 110), font, 1.5, (0, 0, 0), 3, cv2.LINE_AA)
    else:
        # If the format is different, just display as is
        cv2.putText(img, text, (100, 110), font, 1.5, (0, 0, 0), 3, cv2.LINE_AA)

    # Save the image
    cv2.imwrite(output_path, img)
    print(f"Created Indian license plate image at {output_path}")

    return output_path

def create_multiple_indian_plates():
    """Create multiple variations of the license plate for testing"""
    # Original format
    create_indian_license_plate("GJ03ER0563", "ocr_feedback/images/indian_plate1.jpg")

    # With spaces for better OCR
    create_indian_license_plate("GJ 03 ER 0563", "ocr_feedback/images/indian_plate2.jpg")

    # Different font size and positioning
    img = np.ones((200, 500, 3), np.uint8) * 255
    cv2.rectangle(img, (10, 10), (490, 190), (0, 0, 0), 2)
    cv2.rectangle(img, (15, 15), (485, 185), (255, 220, 0), -1)
    cv2.rectangle(img, (20, 20), (70, 50), (255, 255, 255), -1)

    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "IND", (25, 42), font, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, "GJ 03", (90, 110), font, 1.8, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(img, "ER 0563", (230, 110), font, 1.8, (0, 0, 0), 4, cv2.LINE_AA)

    os.makedirs(os.path.dirname("ocr_feedback/images/indian_plate3.jpg"), exist_ok=True)
    cv2.imwrite("ocr_feedback/images/indian_plate3.jpg", img)
    print(f"Created Indian license plate image at ocr_feedback/images/indian_plate3.jpg")

if __name__ == "__main__":
    # Create multiple variations of the Indian license plate
    create_multiple_indian_plates()
