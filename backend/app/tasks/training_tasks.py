import os
from celery import Celery
from datetime import datetime
from sqlalchemy.orm import Session

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "retail_shelf_ai",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
)


@celery_app.task(bind=True, name="train_model")
def train_model_task(self, company_id: int, dataset_id: int, model_name: str, config: dict):
    """
    Background task for training YOLO model
    """
    from app.models.database import SessionLocal, Model, Dataset
    from app.ai.yolo_trainer import YOLOTrainer
    
    db = SessionLocal()
    
    try:
        # Update model status to training
        model = db.query(Model).filter(
            Model.company_id == company_id,
            Model.name == model_name
        ).first()
        
        if not model:
            # Create new model record
            model = Model(
                company_id=company_id,
                dataset_id=dataset_id,
                name=model_name,
                version="1.0",
                status="training",
                training_started_at=datetime.utcnow(),
                training_config=config
            )
            db.add(model)
            db.commit()
            db.refresh(model)
        else:
            model.status = "training"
            model.training_started_at = datetime.utcnow()
            model.training_config = config
            db.commit()
        
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset or not dataset.yaml_path:
            raise Exception("Dataset not ready for training")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': config.get('epochs', 50), 'status': 'Starting training...'}
        )
        
        # Initialize trainer
        trainer = YOLOTrainer(company_id, dataset_id)
        
        # Train model
        result = trainer.train(
            yaml_path=dataset.yaml_path,
            epochs=config.get('epochs', 50),
            batch=config.get('batch', 16),
            imgsz=config.get('imgsz', 640)
        )
        
        if result['success']:
            # Update model with results
            model.status = "completed"
            model.model_path = result['model_path']
            model.training_completed_at = datetime.utcnow()
            model.training_metrics = result.get('metrics', {})
            
            # Update individual metrics
            metrics = result.get('metrics', {})
            model.mAP50 = metrics.get('mAP50', 0)
            model.mAP50_95 = metrics.get('mAP50-95', 0)
            model.precision = metrics.get('precision', 0)
            model.recall = metrics.get('recall', 0)
            
            db.commit()
            
            return {
                'status': 'completed',
                'model_id': model.id,
                'model_path': result['model_path'],
                'metrics': metrics
            }
        else:
            # Training failed
            model.status = "failed"
            model.training_completed_at = datetime.utcnow()
            db.commit()
            
            raise Exception(f"Training failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        # Update model status to failed
        if model:
            model.status = "failed"
            db.commit()
        
        db.close()
        raise e
    
    finally:
        db.close()


@celery_app.task(bind=True, name="analyze_image")
def analyze_image_task(self, company_id: int, model_id: int, image_path: str):
    """
    Background task for analyzing shelf image
    """
    from app.models.database import SessionLocal, Analysis, Model, Product
    from app.ai.yolo_inference import YOLOInference
    from app.ai.shelf_analyzer import ShelfAnalyzer
    from app.ai.color_analyzer import ColorAnalyzer
    from app.ai.scoring_engine import ScoringEngine
    
    db = SessionLocal()
    
    try:
        # Get model
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model or not model.model_path:
            raise Exception("Model not found or not trained")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Running inference...'}
        )
        
        # Initialize inference
        inference = YOLOInference(model.model_path)
        
        # Run detection
        result = inference.predict(image_path, conf_threshold=0.25)
        
        if not result['success']:
            raise Exception(f"Inference failed: {result.get('error')}")
        
        detections = result['detections']
        image_shape = result['image_shape']
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Analyzing shelf...'}
        )
        
        # Analyze shelf
        analyzer = ShelfAnalyzer(image_shape)
        shelf_analysis = analyzer.analyze_shelf(detections, image_shape)
        
        # Color analysis
        color_analyzer = ColorAnalyzer()
        color_results = color_analyzer.extract_dominant_colors(image_path)
        
        # Get product reference colors for comparison
        color_matches = {}
        if detections:
            for det in detections:
                class_name = det['class_name']
                product = db.query(Product).filter(
                    Product.company_id == company_id,
                    Product.name == class_name
                ).first()
                
                if product and product.reference_colors:
                    color_result = color_analyzer.analyze_product_colors(
                        image_path,
                        det['bbox'],
                        product.reference_colors
                    )
                    if color_result['success']:
                        color_matches[class_name] = color_result['color_match_scores']
        
        # Calculate scores
        scoring = ScoringEngine()
        metrics = {
            'shelf_coverage': shelf_analysis['shelf_coverage'],
            'visibility_score': shelf_analysis['visibility_score'],
            'actual_distribution': shelf_analysis['distribution'],
            'expected_distribution': {'left': 33, 'center': 34, 'right': 33},  # Default
            'color_matches': color_matches
        }
        
        score_result = scoring.calculate_total_score(metrics)
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Saving results...'}
        )
        
        # Create analysis record
        analysis = Analysis(
            company_id=company_id,
            model_id=model_id,
            image_path=image_path,
            detections=detections,
            total_products=shelf_analysis['total_products'],
            product_counts=shelf_analysis['product_counts'],
            shelf_coverage=shelf_analysis['shelf_coverage'],
            color_analysis=color_results if color_results['success'] else None,
            visibility_score=shelf_analysis['visibility_score'],
            planogram_score=score_result['component_scores']['planogram_compliance'],
            total_score=score_result['total_score'],
            analysis_date=datetime.utcnow()
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        return {
            'status': 'completed',
            'analysis_id': analysis.id,
            'total_products': shelf_analysis['total_products'],
            'product_counts': shelf_analysis['product_counts'],
            'shelf_coverage': shelf_analysis['shelf_coverage'],
            'total_score': score_result['total_score'],
            'component_scores': score_result['component_scores']
        }
    
    except Exception as e:
        db.close()
        raise e
    
    finally:
        db.close()


@celery_app.task(name="test_task")
def test_task():
    """Simple test task"""
    return {"status": "success", "message": "Celery is working!"}
