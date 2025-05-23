#!/usr/bin/env python3
"""
Script to run the original NumberPlate-Detection-Extraction app.py
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('run_original_app')

def main():
    # Check if the NumberPlate-Detection-Extraction directory exists
    project_dir = "./NumberPlate-Detection-Extraction"
    if not os.path.exists(project_dir):
        logger.error(f"Project directory not found: {project_dir}")
        return 1
    
    # Check if app.py exists
    app_path = os.path.join(project_dir, "app.py")
    if not os.path.exists(app_path):
        logger.error(f"app.py not found at: {app_path}")
        return 1
    
    # Check if the static/models directory exists
    models_dir = os.path.join(project_dir, "static/models")
    if not os.path.exists(models_dir):
        logger.error(f"Models directory not found: {models_dir}")
        return 1
    
    # Check if the YOLO model exists
    model_path = os.path.join(models_dir, "best.onnx")
    if not os.path.exists(model_path):
        logger.error(f"YOLO model not found at: {model_path}")
        return 1
    
    # Run the app.py script
    logger.info(f"Running the original app.py from: {app_path}")
    logger.info("Access the web interface at: http://localhost:5000")
    logger.info("Upload images from the test_images directory to see the results")
    
    # Change to the project directory
    os.chdir(project_dir)
    
    # Run the app.py script
    try:
        subprocess.run(["python", "app.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running app.py: {str(e)}")
        return 1
    except KeyboardInterrupt:
        logger.info("App stopped by user")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
