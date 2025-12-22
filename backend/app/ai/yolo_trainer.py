import os
from ultralytics import YOLO
from pathlib import Path
import yaml
from datetime import datetime


class YOLOTrainer:
    def __init__(self, company_id: int, dataset_id: int):
        self.company_id = company_id
        self.dataset_id = dataset_id
        self.base_model = os.getenv("BASE_YOLO_MODEL", "yolov8n.pt")
        self.models_dir = Path(os.getenv("MODELS_DIR", "./models"))
        self.datasets_dir = Path(os.getenv("DATASETS_DIR", "./datasets"))
        
        # Create company model directory
        self.company_model_dir = self.models_dir / f"company_{company_id}"
        self.company_model_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_dataset(self, classes: list):
        """Prepare dataset.yaml for training"""
        dataset_path = self.datasets_dir / f"company_{self.company_id}" / f"dataset_{self.dataset_id}"
        dataset_path.mkdir(parents=True, exist_ok=True)
        
        # Create data.yaml
        data_yaml = {
            'path': str(dataset_path.absolute()),
            'train': 'images/train',
            'val': 'images/val',
            'names': {i: name for i, name in enumerate(classes)},
            'nc': len(classes)
        }
        
        yaml_path = dataset_path / "data.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(data_yaml, f)
        
        return str(yaml_path)
    
    def train(self, yaml_path: str, epochs: int = 50, batch: int = 16, imgsz: int = 640):
        """Train YOLO model"""
        try:
            # Load base model
            model = YOLO(self.base_model)
            
            # Train
            results = model.train(
                data=yaml_path,
                epochs=epochs,
                batch=batch,
                imgsz=imgsz,
                project=str(self.company_model_dir),
                name=f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                patience=10,
                save=True,
                device='cuda' if os.system('nvidia-smi') == 0 else 'cpu'
            )
            
            # Get best model path
            best_model_path = results.save_dir / "weights" / "best.pt"
            
            # Copy to company models
            final_model_path = self.company_model_dir / f"model_dataset_{self.dataset_id}.pt"
            if best_model_path.exists():
                import shutil
                shutil.copy(best_model_path, final_model_path)
            
            # Extract metrics
            metrics = {
                'mAP50': float(results.results_dict.get('metrics/mAP50(B)', 0)),
                'mAP50-95': float(results.results_dict.get('metrics/mAP50-95(B)', 0)),
                'precision': float(results.results_dict.get('metrics/precision(B)', 0)),
                'recall': float(results.results_dict.get('metrics/recall(B)', 0))
            }
            
            return {
                'success': True,
                'model_path': str(final_model_path),
                'metrics': metrics,
                'training_dir': str(results.save_dir)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate(self, model_path: str, yaml_path: str):
        """Validate trained model"""
        try:
            model = YOLO(model_path)
            results = model.val(data=yaml_path)
            
            return {
                'success': True,
                'metrics': {
                    'mAP50': float(results.results_dict.get('metrics/mAP50(B)', 0)),
                    'mAP50-95': float(results.results_dict.get('metrics/mAP50-95(B)', 0)),
                    'precision': float(results.results_dict.get('metrics/precision(B)', 0)),
                    'recall': float(results.results_dict.get('metrics/recall(B)', 0))
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
