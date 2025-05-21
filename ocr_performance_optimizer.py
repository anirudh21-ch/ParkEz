import os
import time
import json
import cv2
import numpy as np
from functools import lru_cache
import threading
import queue

class OCRPerformanceOptimizer:
    """
    Performance optimizer for OCR operations
    """
    
    def __init__(self, cache_size=100, max_workers=4):
        """
        Initialize the performance optimizer
        
        Args:
            cache_size: Size of the LRU cache for OCR results
            max_workers: Maximum number of worker threads for parallel processing
        """
        self.cache_size = cache_size
        self.max_workers = max_workers
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_processing_time": 0,
            "total_images_processed": 0,
            "parallel_tasks_executed": 0
        }
        
        # Initialize worker threads and task queue
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.workers = []
        
        # Start worker threads
        for _ in range(max_workers):
            worker = threading.Thread(target=self._worker_thread, daemon=True)
            worker.start()
            self.workers.append(worker)
    
    @lru_cache(maxsize=100)
    def cached_ocr(self, image_hash, config):
        """
        Placeholder for cached OCR function
        This will be replaced with actual implementation
        """
        return None
    
    def _worker_thread(self):
        """
        Worker thread for parallel processing
        """
        while True:
            try:
                # Get task from queue
                task_id, task_func, args, kwargs = self.task_queue.get()
                
                # Execute task
                start_time = time.time()
                try:
                    result = task_func(*args, **kwargs)
                    success = True
                except Exception as e:
                    result = str(e)
                    success = False
                
                processing_time = time.time() - start_time
                
                # Put result in result queue
                self.result_queue.put((task_id, result, success, processing_time))
                
                # Mark task as done
                self.task_queue.task_done()
                
                # Update stats
                self.stats["parallel_tasks_executed"] += 1
                self.stats["total_processing_time"] += processing_time
            
            except Exception as e:
                print(f"Error in worker thread: {str(e)}")
    
    def submit_task(self, task_func, *args, **kwargs):
        """
        Submit a task for parallel processing
        
        Args:
            task_func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Task ID
        """
        task_id = hash(str(time.time()) + str(args) + str(kwargs))
        self.task_queue.put((task_id, task_func, args, kwargs))
        return task_id
    
    def get_result(self, task_id, timeout=None):
        """
        Get the result of a task
        
        Args:
            task_id: Task ID
            timeout: Timeout in seconds
            
        Returns:
            Task result
        """
        try:
            # Wait for result
            while True:
                try:
                    result_task_id, result, success, processing_time = self.result_queue.get(timeout=timeout)
                    
                    # Check if this is the result we're looking for
                    if result_task_id == task_id:
                        return result, success, processing_time
                    
                    # Put back other results
                    self.result_queue.put((result_task_id, result, success, processing_time))
                    
                except queue.Empty:
                    return None, False, 0
        
        except Exception as e:
            print(f"Error getting result: {str(e)}")
            return None, False, 0
    
    def optimize_image(self, image, target_size=800):
        """
        Optimize image for OCR processing
        
        Args:
            image: OpenCV image
            target_size: Target size for the largest dimension
            
        Returns:
            Optimized image
        """
        # Check if image needs resizing
        height, width = image.shape[:2]
        max_dim = max(height, width)
        
        if max_dim > target_size:
            # Calculate scaling factor
            scale = target_size / max_dim
            
            # Resize image
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            return resized
        
        return image
    
    def compute_image_hash(self, image):
        """
        Compute a hash for an image
        
        Args:
            image: OpenCV image
            
        Returns:
            Image hash
        """
        # Resize image to a small size for hashing
        small_image = cv2.resize(image, (32, 32), interpolation=cv2.INTER_AREA)
        
        # Convert to grayscale
        gray = cv2.cvtColor(small_image, cv2.COLOR_BGR2GRAY)
        
        # Compute average pixel value
        avg_pixel = gray.mean()
        
        # Compute hash
        hash_value = 0
        for i in range(32):
            for j in range(32):
                if gray[i, j] > avg_pixel:
                    hash_value += 1 << (i * 32 + j)
        
        return hash_value
    
    def get_stats(self):
        """
        Get performance statistics
        
        Returns:
            Dictionary with performance statistics
        """
        # Calculate average processing time
        avg_time = 0
        if self.stats["total_images_processed"] > 0:
            avg_time = self.stats["total_processing_time"] / self.stats["total_images_processed"]
        
        # Calculate cache hit rate
        cache_hit_rate = 0
        total_cache_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total_cache_requests > 0:
            cache_hit_rate = self.stats["cache_hits"] / total_cache_requests
        
        return {
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "cache_hit_rate": cache_hit_rate,
            "total_processing_time": self.stats["total_processing_time"],
            "total_images_processed": self.stats["total_images_processed"],
            "average_processing_time": avg_time,
            "parallel_tasks_executed": self.stats["parallel_tasks_executed"],
            "active_workers": len(self.workers),
            "task_queue_size": self.task_queue.qsize(),
            "result_queue_size": self.result_queue.qsize()
        }
