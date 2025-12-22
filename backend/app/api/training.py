from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.models.database import get_db, Model, Dataset, Company
from app.tasks.training_tasks import train_model_task, celery_app

router = APIRouter()


class TrainingRequest(BaseModel):
    company_id: int
    dataset_id: int
    model_name: str
    epochs: int = 50
    batch_size: int = 16
    image_size: int = 640


class TrainingResponse(BaseModel):
    task_id: str
    model_id: int
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    status: Optional[str] = None
    result: Optional[dict] = None


# Start Training
@router.post("/start", response_model=TrainingResponse)
def start_training(request: TrainingRequest, db: Session = Depends(get_db)):
    # Validate company
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Validate dataset
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.status != "ready":
        raise HTTPException(status_code=400, detail="Dataset is not ready for training")
    
    # Create model record
    model = Model(
        company_id=request.company_id,
        dataset_id=request.dataset_id,
        name=request.model_name,
        version="1.0",
        status="pending",
        training_config={
            'epochs': request.epochs,
            'batch': request.batch_size,
            'imgsz': request.image_size
        }
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    
    # Start Celery task
    config = {
        'epochs': request.epochs,
        'batch': request.batch_size,
        'imgsz': request.image_size
    }
    
    task = train_model_task.delay(
        request.company_id,
        request.dataset_id,
        request.model_name,
        config
    )
    
    return TrainingResponse(
        task_id=task.id,
        model_id=model.id,
        status="started",
        message="Training started successfully"
    )


# Get Task Status
@router.get("/status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    task = celery_app.AsyncResult(task_id)
    
    response = {
        'task_id': task_id,
        'state': task.state,
        'status': None,
        'result': None
    }
    
    if task.state == 'PENDING':
        response['status'] = 'Task is waiting to start'
    elif task.state == 'STARTED':
        response['status'] = 'Task has started'
    elif task.state == 'PROGRESS':
        response['status'] = str(task.info.get('status', ''))
        response['result'] = task.info
    elif task.state == 'SUCCESS':
        response['status'] = 'Task completed successfully'
        response['result'] = task.result
    elif task.state == 'FAILURE':
        response['status'] = f'Task failed: {str(task.info)}'
    
    return TaskStatusResponse(**response)


# Get Model Training History
@router.get("/history/company/{company_id}")
def get_training_history(company_id: int, db: Session = Depends(get_db)):
    models = db.query(Model).filter(Model.company_id == company_id).all()
    
    history = []
    for model in models:
        history.append({
            'id': model.id,
            'name': model.name,
            'status': model.status,
            'mAP50': model.mAP50,
            'precision': model.precision,
            'recall': model.recall,
            'training_started': model.training_started_at,
            'training_completed': model.training_completed_at
        })
    
    return history


# Test Celery Connection
@router.get("/test-celery")
def test_celery():
    from app.tasks.training_tasks import test_task
    task = test_task.delay()
    return {
        'task_id': task.id,
        'message': 'Test task submitted',
        'status': task.state
    }
