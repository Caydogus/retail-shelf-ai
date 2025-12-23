from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import shutil
import uuid

from app.models.database import get_db, Product, Company

router = APIRouter()

# Ürün resimleri için klasör
PRODUCT_IMAGES_DIR = r"C:\Users\recepuce\Desktop\images"
os.makedirs(PRODUCT_IMAGES_DIR, exist_ok=True)


# Pydantic Schemas
class ProductResponse(BaseModel):
    id: int
    company_id: int
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    reference_image: Optional[str] = None
    is_own_product: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Create Product
@router.post("/", response_model=ProductResponse)
async def create_product(
    name: str = Form(...),
    brand: str = Form(...),
    category: str = Form(""),
    is_own_product: bool = Form(True),
    reference_image: UploadFile = File(...),
    company_id: int = Form(1),
    db: Session = Depends(get_db)
):
    # Şirket kontrolü
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    try:
        # Dosya adı oluştur (unique)
        file_ext = os.path.splitext(reference_image.filename)[1]
        safe_name = name.replace(' ', '_').replace('/', '_')
        unique_filename = f"{safe_name}_{uuid.uuid4().hex[:8]}{file_ext}"
        file_path = os.path.join(PRODUCT_IMAGES_DIR, unique_filename)
        
        # Dosyayı kaydet
        with open(file_path, "wb") as buffer:
            content = await reference_image.read()
            buffer.write(content)
        
        # Ürün oluştur
        new_product = Product(
            company_id=company_id,
            name=name,
            brand=brand,
            category=category if category else None,
            reference_image=file_path,
            is_own_product=is_own_product
        )
        
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        return new_product
        
    except Exception as e:
        db.rollback()
        # Hata durumunda dosyayı sil
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")


# Get Company Products
@router.get("/", response_model=List[ProductResponse])
def get_products(
    company_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    
    if company_id:
        query = query.filter(Product.company_id == company_id)
    
    products = query.all()
    return products


# Get Product by ID
@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# Update Product
@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    is_own_product: Optional[bool] = Form(None),
    reference_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        # Update fields
        if name is not None:
            product.name = name
        if brand is not None:
            product.brand = brand
        if category is not None:
            product.category = category
        if is_own_product is not None:
            product.is_own_product = is_own_product
        
        # Update image if provided
        if reference_image:
            # Delete old image
            if product.reference_image and os.path.exists(product.reference_image):
                os.remove(product.reference_image)
            
            # Save new image
            file_ext = os.path.splitext(reference_image.filename)[1]
            safe_name = product.name.replace(' ', '_').replace('/', '_')
            unique_filename = f"{safe_name}_{uuid.uuid4().hex[:8]}{file_ext}"
            file_path = os.path.join(PRODUCT_IMAGES_DIR, unique_filename)
            
            with open(file_path, "wb") as buffer:
                content = await reference_image.read()
                buffer.write(content)
            
            product.reference_image = file_path
        
        product.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(product)
        
        return product
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")


# Delete Product
@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        # Delete image file
        if product.reference_image and os.path.exists(product.reference_image):
            os.remove(product.reference_image)
        
        # Delete from database
        db.delete(product)
        db.commit()
        
        return {"message": "Product deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")
