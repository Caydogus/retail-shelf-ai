from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import shutil

from app.models.database import get_db, Company

router = APIRouter()


# Pydantic Schemas
class CompanyCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Create Company
@router.post("/", response_model=CompanyResponse)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    # Check if company exists
    existing = db.query(Company).filter(Company.name == company.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company already exists")
    
    new_company = Company(
        name=company.name,
        description=company.description
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company


# Get All Companies
@router.get("/", response_model=List[CompanyResponse])
def get_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    companies = db.query(Company).filter(Company.is_active == True).order_by(Company.id).offset(skip).limit(limit).all()
    return companies


# Get Company by ID
@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


# Update Company
@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: int, company: CompanyCreate, db: Session = Depends(get_db)):
    db_company = db.query(Company).filter(Company.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db_company.name = company.name
    db_company.description = company.description
    db_company.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_company)
    return db_company


# Delete Company
@router.delete("/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.is_active = False
    company.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Company deleted successfully"}


# Upload Company Logo
@router.post("/{company_id}/logo")
def upload_logo(company_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Create upload directory
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    logo_dir = os.path.join(upload_dir, "company_logos")
    os.makedirs(logo_dir, exist_ok=True)
    
    # Save file
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"company_{company_id}{file_ext}"
    file_path = os.path.join(logo_dir, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update company
    company.logo_url = f"/uploads/company_logos/{filename}"
    company.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Logo uploaded successfully", "logo_url": company.logo_url}