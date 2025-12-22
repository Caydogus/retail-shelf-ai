import os
from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path


class YOLOInference:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.model = YOLO(model_path)
        self.model_path = model_path
    
    def predict(self, image_path: str, conf_threshold: float = 0.25):
        """Run inference on image"""
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Cannot read image: {image_path}")
            
            # Run inference
            results = self.model.predict(
                source=image,
                conf=conf_threshold,
                save=False,
                verbose=False
            )
            
            # Parse results
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    detection = {
                        'class_id': int(box.cls[0]),
                        'class_name': result.names[int(box.cls[0])],
                        'confidence': float(box.conf[0]),
                        'bbox': box.xyxy[0].tolist(),  # [x1, y1, x2, y2]
                        'bbox_normalized': box.xywhn[0].tolist()  # [x_center, y_center, width, height] normalized
                    }
                    detections.append(detection)
            
            return {
                'success': True,
                'detections': detections,
                'image_shape': image.shape,
                'total_detections': len(detections)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict_batch(self, image_paths: list, conf_threshold: float = 0.25):
        """Run inference on multiple images"""
        results_list = []
        for image_path in image_paths:
            result = self.predict(image_path, conf_threshold)
            results_list.append({
                'image_path': image_path,
                'result': result
            })
        return results_list
    
    def draw_detections(self, image_path: str, detections: list, output_path: str = None):
        """Draw bounding boxes on image"""
        image = cv2.imread(image_path)
        
        for det in detections:
            bbox = det['bbox']
            x1, y1, x2, y2 = map(int, bbox)
            
            # Draw box
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"{det['class_name']}: {det['confidence']:.2f}"
            cv2.putText(image, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        if output_path:
            cv2.imwrite(output_path, image)
        
        return image
