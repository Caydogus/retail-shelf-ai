import os
import shutil
import yaml
import json
from pathlib import Path
from typing import List, Dict
import random


class DatasetBuilder:
    def __init__(self, company_id: int, dataset_id: int):
        self.company_id = company_id
        self.dataset_id = dataset_id
        self.datasets_dir = Path(os.getenv("DATASETS_DIR", "./datasets"))
        
        # Create dataset directory structure
        self.dataset_path = self.datasets_dir / f"company_{company_id}" / f"dataset_{dataset_id}"
        self.images_dir = self.dataset_path / "images"
        self.labels_dir = self.dataset_path / "labels"
        
        # Create subdirectories
        (self.images_dir / "train").mkdir(parents=True, exist_ok=True)
        (self.images_dir / "val").mkdir(parents=True, exist_ok=True)
        (self.labels_dir / "train").mkdir(parents=True, exist_ok=True)
        (self.labels_dir / "val").mkdir(parents=True, exist_ok=True)
    
    def add_annotated_image(self, image_path: str, annotations: List[Dict], split: str = "train"):
        '''Add annotated image to dataset'''
        try:
            # Validate split
            if split not in ["train", "val"]:
                return {'success': False, 'error': 'Invalid split. Use train or val'}
            
            # Copy image
            image_name = Path(image_path).name
            dest_image = self.images_dir / split / image_name
            shutil.copy(image_path, dest_image)
            
            # Create YOLO format label file
            label_name = Path(image_path).stem + ".txt"
            dest_label = self.labels_dir / split / label_name
            
            # Convert annotations to YOLO format
            label_lines = []
            for ann in annotations:
                # YOLO format: class_id x_center y_center width height (all normalized)
                class_id = ann['class_id']
                x_center = ann['x_center']
                y_center = ann['y_center']
                width = ann['width']
                height = ann['height']
                
                label_lines.append(f"{class_id} {x_center} {y_center} {width} {height}")
            
            # Write label file
            with open(dest_label, 'w') as f:
                f.write('\n'.join(label_lines))
            
            return {'success': True, 'image_path': str(dest_image), 'label_path': str(dest_label)}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_data_yaml(self, class_names: List[str]):
        '''Create data.yaml for YOLOv8 training'''
        try:
            data = {
                'path': str(self.dataset_path.absolute()),
                'train': 'images/train',
                'val': 'images/val',
                'names': {i: name for i, name in enumerate(class_names)},
                'nc': len(class_names)
            }
            
            yaml_path = self.dataset_path / "data.yaml"
            with open(yaml_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            
            return {'success': True, 'yaml_path': str(yaml_path)}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def split_dataset(self, train_ratio: float = 0.8):
        '''Split dataset into train and val'''
        try:
            # Get all images from train directory
            train_images = list((self.images_dir / "train").glob("*.*"))
            
            if not train_images:
                return {'success': False, 'error': 'No images found in train directory'}
            
            # Shuffle and split
            random.shuffle(train_images)
            split_idx = int(len(train_images) * train_ratio)
            
            val_images = train_images[split_idx:]
            
            # Move validation images
            for img_path in val_images:
                # Move image
                dest_img = self.images_dir / "val" / img_path.name
                shutil.move(str(img_path), str(dest_img))
                
                # Move corresponding label
                label_name = img_path.stem + ".txt"
                src_label = self.labels_dir / "train" / label_name
                dest_label = self.labels_dir / "val" / label_name
                
                if src_label.exists():
                    shutil.move(str(src_label), str(dest_label))
            
            train_count = split_idx
            val_count = len(val_images)
            
            return {
                'success': True,
                'train_images': train_count,
                'val_images': val_count,
                'total_images': len(train_images)
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_dataset_stats(self):
        '''Get dataset statistics'''
        try:
            train_images = len(list((self.images_dir / "train").glob("*.*")))
            val_images = len(list((self.images_dir / "val").glob("*.*")))
            train_labels = len(list((self.labels_dir / "train").glob("*.txt")))
            val_labels = len(list((self.labels_dir / "val").glob("*.txt")))
            
            # Count annotations per class
            class_counts = {}
            for label_file in (self.labels_dir / "train").glob("*.txt"):
                with open(label_file, 'r') as f:
                    for line in f:
                        class_id = int(line.split()[0])
                        class_counts[class_id] = class_counts.get(class_id, 0) + 1
            
            return {
                'success': True,
                'train_images': train_images,
                'val_images': val_images,
                'total_images': train_images + val_images,
                'train_labels': train_labels,
                'val_labels': val_labels,
                'annotated_images': train_labels + val_labels,
                'class_distribution': class_counts
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_dataset(self):
        '''Validate dataset structure and annotations'''
        issues = []
        
        try:
            # Check if directories exist
            if not self.images_dir.exists():
                issues.append("Images directory missing")
            if not self.labels_dir.exists():
                issues.append("Labels directory missing")
            
            # Check train/val splits
            for split in ["train", "val"]:
                img_dir = self.images_dir / split
                lbl_dir = self.labels_dir / split
                
                if not img_dir.exists():
                    issues.append(f"{split} images directory missing")
                    continue
                
                images = list(img_dir.glob("*.*"))
                labels = list(lbl_dir.glob("*.txt"))
                
                # Check if every image has a label
                for img in images:
                    label_path = lbl_dir / (img.stem + ".txt")
                    if not label_path.exists():
                        issues.append(f"Missing label for {img.name}")
                
                # Check if labels are valid
                for label in labels:
                    with open(label, 'r') as f:
                        for line_num, line in enumerate(f, 1):
                            parts = line.strip().split()
                            if len(parts) != 5:
                                issues.append(f"Invalid format in {label.name} line {line_num}")
            
            # Check data.yaml
            yaml_path = self.dataset_path / "data.yaml"
            if not yaml_path.exists():
                issues.append("data.yaml file missing")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues
            }
        
        except Exception as e:
            return {'valid': False, 'issues': [str(e)]}
    
    def export_dataset_info(self):
        '''Export dataset information to JSON'''
        try:
            stats = self.get_dataset_stats()
            validation = self.validate_dataset()
            
            info = {
                'company_id': self.company_id,
                'dataset_id': self.dataset_id,
                'dataset_path': str(self.dataset_path),
                'statistics': stats,
                'validation': validation,
                'created_at': str(Path(self.dataset_path).stat().st_ctime)
            }
            
            info_path = self.dataset_path / "dataset_info.json"
            with open(info_path, 'w') as f:
                json.dump(info, f, indent=2)
            
            return {'success': True, 'info_path': str(info_path), 'info': info}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
