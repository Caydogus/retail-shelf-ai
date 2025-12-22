from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import shutil

from app.models.database import get_db, Dataset, Company

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


# ============================================================================
# YENİ: TOPLU UPLOAD ENDPOİNT
# ============================================================================

@router.post("/upload")
async def upload_dataset_bulk(
    files: List[UploadFile] = File(...),
    dataset_name: str = "New Dataset",
    company_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Toplu fotoğraf yükle ve dataset oluştur
    Frontend'den direkt kullanılır
    """
    try:
        # Company kontrolü
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company bulunamadı")
        
        # Dataset oluştur
        new_dataset = Dataset(
            company_id=company_id,
            name=dataset_name,
            description=f"{len(files)} fotoğraf içeren dataset",
            status="preparing",
            total_images=0,
            annotated_images=0,
            train_images=0,
            val_images=0
        )
        db.add(new_dataset)
        db.commit()
        db.refresh(new_dataset)
        
        # Klasör oluştur
        upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        dataset_dir = os.path.join(upload_dir, "datasets", f"company_{company_id}", f"dataset_{new_dataset.id}")
        images_dir = os.path.join(dataset_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Dosyaları kaydet
        uploaded_files = []
        for file in files:
            # Dosya uzantısı kontrolü
            if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            
            file_path = os.path.join(images_dir, file.filename)
            
            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                uploaded_files.append({
                    'filename': file.filename,
                    'size': os.path.getsize(file_path)
                })
            except Exception as e:
                print(f"Dosya yükleme hatası ({file.filename}): {e}")
                continue
        
        # Dataset güncelle
        new_dataset.dataset_path = dataset_dir
        new_dataset.total_images = len(uploaded_files)
        new_dataset.status = "uploaded"
        db.commit()
        
        return {
            "success": True,
            "message": f"{len(uploaded_files)} fotoğraf yüklendi",
            "dataset_id": new_dataset.id,
            "dataset_name": dataset_name,
            "uploaded_files": uploaded_files,
            "total_images": len(uploaded_files)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Yükleme hatası: {str(e)}")


# ============================================================================
# MEVCUT ENDPOİNTLER
# ============================================================================

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
        status="preparing",
        total_images=0,
        annotated_images=0,
        train_images=0,
        val_images=0
    )
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)
    
    return new_dataset


# Get Company Datasets
@router.get("/company/{company_id}")
def get_company_datasets(company_id: int, db: Session = Depends(get_db)):
    """
    Şirketin tüm dataset'lerini listele
    """
    datasets = db.query(Dataset).filter(
        Dataset.company_id == company_id
    ).order_by(Dataset.created_at.desc()).all()
    
    return [
        {
            'id': d.id,
            'name': d.name,
            'description': d.description,
            'total_images': d.total_images,
            'image_count': d.total_images,  # Frontend için
            'annotated_images': d.annotated_images,
            'status': d.status,
            'created_at': str(d.created_at) if d.created_at else None
        }
        for d in datasets
    ]


# Get Dataset by ID
@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


# Upload Single Image to Existing Dataset
@router.post("/{dataset_id}/upload-image")
async def upload_image_to_dataset(
    dataset_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Dataset klasörünü kontrol et
    if not dataset.dataset_path:
        upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        dataset_dir = os.path.join(upload_dir, "datasets", f"company_{dataset.company_id}", f"dataset_{dataset_id}")
        images_dir = os.path.join(dataset_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        dataset.dataset_path = dataset_dir
    else:
        images_dir = os.path.join(dataset.dataset_path, "images")
        os.makedirs(images_dir, exist_ok=True)
    
    # Dosyayı kaydet
    file_path = os.path.join(images_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Dataset güncelle
    dataset.total_images += 1
    db.commit()
    
    return {
        "message": "Fotoğraf yüklendi",
        "filename": file.filename,
        "path": file_path,
        "total_images": dataset.total_images
    }


# Get Dataset Statistics
@router.get("/{dataset_id}/stats")
def get_dataset_stats(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {
        "success": True,
        "dataset_id": dataset_id,
        "total_images": dataset.total_images,
        "annotated_images": dataset.annotated_images,
        "train_images": dataset.train_images,
        "val_images": dataset.val_images,
        "status": dataset.status
    }


# Delete Dataset
@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Soft delete
    dataset.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Dataset silindi"}