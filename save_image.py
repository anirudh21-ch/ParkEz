import requests
import os

def download_image(url, save_path):
    """
    Download an image from a URL and save it to the specified path
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Download the image
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Save the image
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Image saved to {save_path}")
        return True
    
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        return False

# URL of the image (replace with the actual URL)
image_url = "https://i.imgur.com/JKYgGVk.jpg"

# Path to save the image
save_path = "ocr_feedback/images/red_car.jpg"

# Download the image
download_image(image_url, save_path)
