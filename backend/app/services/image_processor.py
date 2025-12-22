import os
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import shutil
from typing import Tuple, List


class ImageProcessor:
    def __init__(self, upload_dir: str = None):
        self.upload_dir = upload_dir or os.getenv("UPLOAD_DIR", "./uploads")
    
    def validate_image(self, file_path: str) -> dict:
        '''Validate image file'''
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {'valid': False, 'error': 'File not found'}
            
            # Check file size
            file_size = os.path.getsize(file_path)
            max_size = int(os.getenv("MAX_UPLOAD_SIZE", 10485760))  # 10MB default
            
            if file_size > max_size:
                return {'valid': False, 'error': f'File too large. Max size: {max_size} bytes'}
            
            # Try to open image
            img = Image.open(file_path)
            img.verify()
            
            # Reopen for actual check (verify closes the file)
            img = Image.open(file_path)
            width, height = img.size
            
            # Check minimum dimensions
            if width < 100 or height < 100:
                return {'valid': False, 'error': 'Image too small. Minimum 100x100 pixels'}
            
            return {
                'valid': True,
                'width': width,
                'height': height,
                'format': img.format,
                'size': file_size
            }
        
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def resize_image(self, input_path: str, output_path: str, target_size: Tuple[int, int] = (640, 640)):
        '''Resize image to target size'''
        try:
            img = cv2.imread(input_path)
            resized = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
            cv2.imwrite(output_path, resized)
            return {'success': True, 'output_path': output_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def crop_image(self, input_path: str, bbox: List[int], output_path: str):
        '''Crop image to bounding box [x1, y1, x2, y2]'''
        try:
            img = cv2.imread(input_path)
            x1, y1, x2, y2 = map(int, bbox)
            cropped = img[y1:y2, x1:x2]
            cv2.imwrite(output_path, cropped)
            return {'success': True, 'output_path': output_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def augment_image(self, input_path: str, output_dir: str, num_augmentations: int = 5):
        '''Apply data augmentation'''
        try:
            import albumentations as A
            
            img = cv2.imread(input_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Define augmentation pipeline
            transform = A.Compose([
                A.RandomBrightnessContrast(p=0.5),
                A.HorizontalFlip(p=0.5),
                A.Rotate(limit=15, p=0.5),
                A.GaussNoise(p=0.3),
                A.RandomGamma(p=0.3)
            ])
            
            os.makedirs(output_dir, exist_ok=True)
            base_name = Path(input_path).stem
            
            augmented_paths = []
            for i in range(num_augmentations):
                augmented = transform(image=img)['image']
                augmented = cv2.cvtColor(augmented, cv2.COLOR_RGB2BGR)
                
                output_path = os.path.join(output_dir, f"{base_name}_aug_{i}.jpg")
                cv2.imwrite(output_path, augmented)
                augmented_paths.append(output_path)
            
            return {'success': True, 'augmented_images': augmented_paths}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_thumbnail(self, input_path: str, output_path: str, size: Tuple[int, int] = (150, 150)):
        '''Create thumbnail'''
        try:
            img = Image.open(input_path)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(output_path)
            return {'success': True, 'output_path': output_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def extract_frames_from_video(self, video_path: str, output_dir: str, fps: int = 1):
        '''Extract frames from video'''
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            cap = cv2.VideoCapture(video_path)
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = int(video_fps / fps)
            
            frame_count = 0
            saved_count = 0
            frames = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    output_path = os.path.join(output_dir, f"frame_{saved_count:04d}.jpg")
                    cv2.imwrite(output_path, frame)
                    frames.append(output_path)
                    saved_count += 1
                
                frame_count += 1
            
            cap.release()
            
            return {'success': True, 'frames': frames, 'total_frames': saved_count}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def batch_process_images(self, input_dir: str, output_dir: str, operation: str, **kwargs):
        '''Process multiple images'''
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
            image_files = [f for f in os.listdir(input_dir) 
                          if Path(f).suffix.lower() in image_extensions]
            
            results = []
            for img_file in image_files:
                input_path = os.path.join(input_dir, img_file)
                output_path = os.path.join(output_dir, img_file)
                
                if operation == 'resize':
                    result = self.resize_image(input_path, output_path, **kwargs)
                elif operation == 'thumbnail':
                    result = self.create_thumbnail(input_path, output_path, **kwargs)
                else:
                    result = {'success': False, 'error': 'Unknown operation'}
                
                results.append({'file': img_file, 'result': result})
            
            return {'success': True, 'processed': len(results), 'results': results}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
