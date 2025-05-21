#!/usr/bin/env python3
"""
Script to run the advanced OCR service
"""

import os
import sys
import time
import argparse
import subprocess
import signal
import threading

def parse_arguments():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description='Run the advanced OCR service')
    
    parser.add_argument('--port', type=int, default=5004,
                        help='Port to run the service on (default: 5004)')
    
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host to bind the service to (default: 0.0.0.0)')
    
    parser.add_argument('--debug', action='store_true',
                        help='Run in debug mode')
    
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of worker threads for parallel processing (default: 4)')
    
    parser.add_argument('--cache-size', type=int, default=200,
                        help='Size of the LRU cache for OCR results (default: 200)')
    
    parser.add_argument('--feedback-dir', type=str, default='ocr_feedback',
                        help='Directory to store feedback data (default: ocr_feedback)')
    
    parser.add_argument('--model-dir', type=str, default='yolo_model',
                        help='Directory to store model files (default: yolo_model)')
    
    return parser.parse_args()

def check_dependencies():
    """
    Check if all required dependencies are installed
    """
    try:
        import cv2
        import numpy
        import pytesseract
        import flask
        import pymongo
        import PIL
        
        print("All required dependencies are installed")
        return True
    
    except ImportError as e:
        print(f"Missing dependency: {str(e)}")
        print("Please install all required dependencies:")
        print("pip install opencv-python numpy pytesseract flask flask-cors pymongo python-dotenv Pillow")
        return False

def check_tesseract():
    """
    Check if Tesseract OCR is installed
    """
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"Tesseract OCR version: {version}")
        return True
    
    except Exception as e:
        print(f"Error checking Tesseract OCR: {str(e)}")
        print("Please install Tesseract OCR:")
        print("  - On macOS: brew install tesseract")
        print("  - On Ubuntu/Debian: apt-get install tesseract-ocr")
        print("  - On Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki")
        return False

def run_service(args):
    """
    Run the advanced OCR service
    """
    # Set environment variables
    os.environ['OCR_PORT'] = str(args.port)
    os.environ['OCR_HOST'] = args.host
    os.environ['OCR_DEBUG'] = str(args.debug).lower()
    os.environ['OCR_WORKERS'] = str(args.workers)
    os.environ['OCR_CACHE_SIZE'] = str(args.cache_size)
    os.environ['OCR_FEEDBACK_DIR'] = args.feedback_dir
    os.environ['OCR_MODEL_DIR'] = args.model_dir
    
    # Run the service
    try:
        print(f"Starting advanced OCR service on {args.host}:{args.port}")
        
        # Import and run the service
        from advanced_ocr_service import app
        app.run(host=args.host, port=args.port, debug=args.debug)
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    
    except Exception as e:
        print(f"Error running service: {str(e)}")
        return False
    
    return True

def main():
    """
    Main entry point
    """
    # Parse arguments
    args = parse_arguments()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check Tesseract OCR
    if not check_tesseract():
        return 1
    
    # Run the service
    if not run_service(args):
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
