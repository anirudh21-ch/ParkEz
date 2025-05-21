import os
import json
import base64
import datetime
import cv2
import numpy as np
from PIL import Image
import io

class OCRFeedbackSystem:
    """
    Feedback system for OCR to improve accuracy over time
    """
    
    def __init__(self, feedback_dir="ocr_feedback"):
        """
        Initialize the feedback system
        
        Args:
            feedback_dir: Directory to store feedback data
        """
        self.feedback_dir = feedback_dir
        self.images_dir = os.path.join(feedback_dir, "images")
        self.feedback_file = os.path.join(feedback_dir, "feedback.json")
        self.feedback_data = {}
        
        # Create directories if they don't exist
        if not os.path.exists(self.feedback_dir):
            os.makedirs(self.feedback_dir)
        
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        
        # Load existing feedback data
        self.load_feedback_data()
    
    def load_feedback_data(self):
        """
        Load feedback data from file
        """
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, "r") as f:
                    self.feedback_data = json.load(f)
                print(f"Loaded {len(self.feedback_data)} feedback entries")
            except Exception as e:
                print(f"Error loading feedback data: {str(e)}")
                self.feedback_data = {}
    
    def save_feedback_data(self):
        """
        Save feedback data to file
        """
        try:
            with open(self.feedback_file, "w") as f:
                json.dump(self.feedback_data, f, indent=2)
            print(f"Saved {len(self.feedback_data)} feedback entries")
            return True
        except Exception as e:
            print(f"Error saving feedback data: {str(e)}")
            return False
    
    def save_image(self, image_data, image_id):
        """
        Save an image to the feedback directory
        
        Args:
            image_data: Base64 encoded image data or OpenCV image
            image_id: Unique ID for the image
            
        Returns:
            Path to the saved image
        """
        try:
            image_path = os.path.join(self.images_dir, f"{image_id}.jpg")
            
            # Handle different image formats
            if isinstance(image_data, str) and image_data.startswith("data:image"):
                # Base64 encoded image
                if "," in image_data:
                    image_data = image_data.split(",")[1]
                
                # Decode base64 to image
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
                image.save(image_path)
            
            elif isinstance(image_data, np.ndarray):
                # OpenCV image
                cv2.imwrite(image_path, image_data)
            
            else:
                raise ValueError("Unsupported image format")
            
            return image_path
        
        except Exception as e:
            print(f"Error saving image: {str(e)}")
            return None
    
    def add_feedback(self, image_data, detected_text, corrected_text=None, confidence=None, processing_time=None, metadata=None):
        """
        Add feedback for an OCR result
        
        Args:
            image_data: Base64 encoded image data or OpenCV image
            detected_text: Text detected by OCR
            corrected_text: Corrected text (if provided by user)
            confidence: Confidence score of the OCR result
            processing_time: Time taken to process the image
            metadata: Additional metadata about the OCR process
            
        Returns:
            Feedback ID
        """
        try:
            # Generate a unique ID for the feedback
            feedback_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(hash(str(detected_text)))[-4:]
            
            # Save the image
            image_path = self.save_image(image_data, feedback_id)
            
            if not image_path:
                print("Failed to save image")
                return None
            
            # Create feedback entry
            feedback_entry = {
                "id": feedback_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "image_path": image_path,
                "detected_text": detected_text,
                "corrected_text": corrected_text,
                "confidence": confidence,
                "processing_time": processing_time,
                "metadata": metadata or {},
                "is_correct": corrected_text is None or corrected_text == detected_text
            }
            
            # Add to feedback data
            self.feedback_data[feedback_id] = feedback_entry
            
            # Save feedback data
            self.save_feedback_data()
            
            print(f"Added feedback entry with ID: {feedback_id}")
            return feedback_id
        
        except Exception as e:
            print(f"Error adding feedback: {str(e)}")
            return None
    
    def update_feedback(self, feedback_id, corrected_text):
        """
        Update feedback with corrected text
        
        Args:
            feedback_id: ID of the feedback entry
            corrected_text: Corrected text provided by user
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if feedback_id not in self.feedback_data:
                print(f"Feedback ID {feedback_id} not found")
                return False
            
            # Update feedback entry
            self.feedback_data[feedback_id]["corrected_text"] = corrected_text
            self.feedback_data[feedback_id]["is_correct"] = corrected_text == self.feedback_data[feedback_id]["detected_text"]
            
            # Save feedback data
            self.save_feedback_data()
            
            print(f"Updated feedback entry with ID: {feedback_id}")
            return True
        
        except Exception as e:
            print(f"Error updating feedback: {str(e)}")
            return False
    
    def get_accuracy_stats(self):
        """
        Get accuracy statistics from feedback data
        
        Returns:
            Dictionary with accuracy statistics
        """
        try:
            total_entries = len(self.feedback_data)
            
            if total_entries == 0:
                return {
                    "total_entries": 0,
                    "correct_entries": 0,
                    "accuracy": 0,
                    "average_confidence": 0
                }
            
            correct_entries = sum(1 for entry in self.feedback_data.values() if entry["is_correct"])
            accuracy = correct_entries / total_entries
            
            # Calculate average confidence
            confidences = [entry["confidence"] for entry in self.feedback_data.values() if entry["confidence"] is not None]
            average_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "total_entries": total_entries,
                "correct_entries": correct_entries,
                "accuracy": accuracy,
                "average_confidence": average_confidence
            }
        
        except Exception as e:
            print(f"Error calculating accuracy stats: {str(e)}")
            return None
