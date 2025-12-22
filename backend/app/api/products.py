from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import shutil

from app.models.database import get_db, Dataset, Company
from app.services.dataset_builder import DatasetBuilder
from app.services.image_processor import ImageProcessor

router = APIRouter()


# Pydantic Schemas
class DatasetCreate(BaseModel):
    company_id: int
    name: str
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    id: int
    company_id: int
    name: str
    description: Optional[str] = None
    total_images: int
    annotated_images: int
    train_images: int
    val_images: int
    classes: Optional[list] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnnotationData(BaseModel):
    class_id: int
    class_name: str
    x_center: float
    y_center: float
    width: float
    height: float


class ImageAnnotation(BaseModel):
    annotations: List[AnnotationData]


# Create Dataset
@router.post("/", response_model=DatasetResponse)
def create_dataset(dataset: DatasetCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == dataset.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    new_dataset = Dataset(
        company_id=dataset.company_id,
        name=dataset.name,
        description=dataset.description,
        status="preparing"
    )
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)
    
    # Initialize dataset builder
    builder = DatasetBuilder(dataset.company_id, new_dataset.id)
    
    # Update dataset paths
    new_dataset.dataset_path = str(builder.dataset_path)
    db.commit()
    
    return new_dataset


# Get Company Datasets
@router.get("/company/{company_id}", response_model=List[DatasetResponse])
def get_company_datasets(company_id: int, db: Session = Depends(get_db)):
    datasets = db.query(Dataset).filter(
        Dataset.company_id == company_id,
        Dataset.is_active == True
    ).all()
    return datasets


# Get Dataset by ID
@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


# Upload Image to Dataset
@router.post("/{dataset_id}/upload-image")
async def upload_image_to_dataset(
    dataset_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Initialize processors
    builder = DatasetBuilder(dataset.company_id, dataset_id)
    processor = ImageProcessor()
    
    # Save temporary file
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    temp_dir = os.path.join(upload_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_path = os.path.join(temp_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Validate image
    validation = processor.validate_image(temp_path)
    if not validation['valid']:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail=validation['error'])
    
    # Copy to dataset (will be annotated later)
    dest_dir = builder.images_dir / "train"
    dest_path = dest_dir / file.filename
    shutil.copy(temp_path, dest_path)
    os.remove(temp_path)
    
    # Update dataset stats
    dataset.total_images += 1
    db.commit()
    
    return {
        "message": "Image uploaded successfully",
        "filename": file.filename,
        "path": str(dest_path),
        "image_info": validation
    }


# Add Annotation to Image
@router.post("/{dataset_id}/annotate/{filename}")
def annotate_image(
    dataset_id: int,
    filename: str,
    annotation: ImageAnnotation,
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    builder = DatasetBuilder(dataset.company_id, dataset_id)
    
    # Find image
    image_path = builder.images_dir / "train" / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Convert annotations to required format
    annotations = [
        {
            'class_id': ann.class_id,
            'x_center': ann.x_center,
            'y_center': ann.y_center,
            'width': ann.width,
            'height': ann.height
        }
        for ann in annotation.annotations
    ]
    
    # Add annotated image
    result = builder.add_annotated_image(str(image_path), annotations, "train")
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    
    # Update dataset stats
    dataset.annotated_images += 1
    db.commit()
    
    return {"message": "Image annotated successfully", "result": result}


# Prepare Dataset (Split and Create YAML)
@router.post("/{dataset_id}/prepare")
def prepare_dataset(
    dataset_id: int,
    classes: List[str],
    train_ratio: float = 0.8,
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    builder = DatasetBuilder(dataset.company_id, dataset_id)
    
    # Split dataset
    split_result = builder.split_dataset(train_ratio)
    if not split_result['success']:
        raise HTTPException(status_code=500, detail=split_result['error'])
    
    # Create data.yaml
    yaml_result = builder.create_data_yaml(classes)
    if not yaml_result['success']:
        raise HTTPException(status_code=500, detail=yaml_result['error'])
    
    # Get statistics
    stats = builder.get_dataset_stats()
    
    # Update dataset
    dataset.train_images = split_result['train_images']
    dataset.val_images = split_result['val_images']
    dataset.classes = classes
    dataset.yaml_path = yaml_result['yaml_path']
    dataset.status = "ready"
    db.commit()
    
    return {
        "message": "Dataset prepared successfully",
        "split": split_result,
        "yaml_path": yaml_result['yaml_path'],
        "statistics": stats
    }


# Get Dataset Statistics
@router.get("/{dataset_id}/stats")
def get_dataset_stats(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    builder = DatasetBuilder(dataset.company_id, dataset_id)
    stats = builder.get_dataset_stats()
    
    if not stats['success']:
        raise HTTPException(status_code=500, detail=stats['error'])
    
    return stats


# Validate Dataset
@router.get("/{dataset_id}/validate")
def validate_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    builder = DatasetBuilder(dataset.company_id, dataset_id)
    validation = builder.validate_dataset()
    
    return validation


# Delete Dataset
@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    dataset.is_active = False
    dataset.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Dataset deleted successfully"}