import cv2
import numpy as np
import os
import urllib.request
import time

class LicensePlateDetector:
    """
    License plate detector using YOLOv4 pre-trained model
    """
    
    def __init__(self):
        """
        Initialize the license plate detector
        """
        self.model_initialized = False
        self.net = None
        self.output_layers = None
        self.classes = None
        
        # Model files
        self.model_dir = "yolo_model"
        self.config_path = os.path.join(self.model_dir, "yolov4-tiny-obj.cfg")
        self.weights_path = os.path.join(self.model_dir, "yolov4-tiny-obj_last.weights")
        self.classes_path = os.path.join(self.model_dir, "obj.names")
        
        # Model URLs
        self.config_url = "https://raw.githubusercontent.com/quangnhat185/Plate_detect_and_recognize/master/cfg/yolov3-tiny_obj.cfg"
        self.weights_url = "https://github.com/quangnhat185/Plate_detect_and_recognize/releases/download/v0.1/yolov3-tiny_obj_last.weights"
        self.classes_url = "https://raw.githubusercontent.com/quangnhat185/Plate_detect_and_recognize/master/cfg/obj.names"
        
        # Create model directory if it doesn't exist
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
    
    def download_model_files(self):
        """
        Download the model files if they don't exist
        """
        try:
            # Download config file
            if not os.path.exists(self.config_path):
                print(f"Downloading config file from {self.config_url}...")
                urllib.request.urlretrieve(self.config_url, self.config_path)
                print("Config file downloaded successfully")
            
            # Download weights file
            if not os.path.exists(self.weights_path):
                print(f"Downloading weights file from {self.weights_url}...")
                urllib.request.urlretrieve(self.weights_url, self.weights_path)
                print("Weights file downloaded successfully")
            
            # Download classes file
            if not os.path.exists(self.classes_path):
                print(f"Downloading classes file from {self.classes_url}...")
                urllib.request.urlretrieve(self.classes_url, self.classes_path)
                print("Classes file downloaded successfully")
            
            return True
        except Exception as e:
            print(f"Error downloading model files: {str(e)}")
            return False
    
    def initialize_model(self):
        """
        Initialize the YOLO model
        """
        try:
            # Download model files if they don't exist
            if not self.download_model_files():
                print("Failed to download model files")
                return False
            
            # Load YOLO
            print("Loading YOLO model...")
            self.net = cv2.dnn.readNet(self.weights_path, self.config_path)
            
            # Get output layer names
            layer_names = self.net.getLayerNames()
            self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
            
            # Load classes
            with open(self.classes_path, "r") as f:
                self.classes = [line.strip() for line in f.readlines()]
            
            print("YOLO model loaded successfully")
            self.model_initialized = True
            return True
        except Exception as e:
            print(f"Error initializing YOLO model: {str(e)}")
            return False
    
    def detect_license_plates(self, image, confidence_threshold=0.5):
        """
        Detect license plates in an image
        
        Args:
            image: OpenCV image
            confidence_threshold: Minimum confidence threshold for detection
            
        Returns:
            List of detected license plate regions (x, y, w, h, confidence)
        """
        # Initialize model if not already initialized
        if not self.model_initialized:
            if not self.initialize_model():
                print("Failed to initialize model")
                return []
        
        # Get image dimensions
        height, width, _ = image.shape
        
        # Preprocess image for YOLO
        blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
        
        # Set input and forward pass
        self.net.setInput(blob)
        start_time = time.time()
        outputs = self.net.forward(self.output_layers)
        inference_time = time.time() - start_time
        
        print(f"YOLO inference time: {inference_time:.2f} seconds")
        
        # Process outputs
        license_plates = []
        
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                # Filter by confidence threshold
                if confidence > confidence_threshold:
                    # Get bounding box coordinates
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    # Calculate top-left corner
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    # Add some padding
                    x = max(0, x - 5)
                    y = max(0, y - 5)
                    w = min(width - x, w + 10)
                    h = min(height - y, h + 10)
                    
                    # Add to license plates list
                    license_plates.append((x, y, w, h, confidence))
        
        # Sort by confidence (highest first)
        license_plates.sort(key=lambda x: x[4], reverse=True)
        
        return license_plates
    
    def extract_license_plate_regions(self, image, confidence_threshold=0.5):
        """
        Detect and extract license plate regions from an image
        
        Args:
            image: OpenCV image
            confidence_threshold: Minimum confidence threshold for detection
            
        Returns:
            List of (plate_image, confidence) tuples
        """
        # Detect license plates
        license_plates = self.detect_license_plates(image, confidence_threshold)
        
        # Extract regions
        plate_regions = []
        
        for x, y, w, h, confidence in license_plates:
            # Extract region
            plate_region = image[y:y+h, x:x+w]
            
            # Add to list
            plate_regions.append((plate_region, confidence))
        
        return plate_regions
