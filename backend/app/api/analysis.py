from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import time
import json

from app.models.database import get_db, Analysis, Model, Company
from app.tasks.training_tasks import analyze_image_task, celery_app

router = APIRouter()


class AnalysisRequest(BaseModel):
    company_id: int
    model_id: int


class AnalysisResponse(BaseModel):
    task_id: str
    message: str


class AnalysisResultResponse(BaseModel):
    id: int
    company_id: int
    model_id: int
    total_products: int
    product_counts: dict
    shelf_coverage: float
    visibility_score: float
    planogram_score: float
    total_score: float
    analysis_date: str

    class Config:
        from_attributes = True


# ============================================================================
# YARDIMCI FONKSİYONLAR
# ============================================================================

def get_company_model(company_id: int, db: Session):
    """
    Şirketin aktif modelini getir
    Yoksa varsayılan modele geri dön
    """
    try:
        # Şirketin aktif modelini bul
        model_record = db.query(Model).filter(
            Model.company_id == company_id,
            Model.is_active == True,
            Model.status == 'completed'
        ).first()
        
        if model_record and model_record.model_path:
            # Model dosyası var mı kontrol et
            if os.path.exists(model_record.model_path):
                model_path = model_record.model_path
                print(f"✅ Şirkete özel model yükleniyor: {model_path}")
                return model_path, model_record
            else:
                print(f"⚠️ Model dosyası bulunamadı: {model_record.model_path}")
        
        # Varsayılan model
        model_path = 'yolov8n.pt'
        print(f"⚠️ Varsayılan model kullanılıyor: {model_path}")
        return model_path, None
        
    except Exception as e:
        print(f"⚠️ Model yükleme hatası: {e}")
        return 'yolov8n.pt', None


# ============================================================================
# UPLOAD AND ANALYZE (CELERY İLE)
# ============================================================================

@router.post("/upload", response_model=AnalysisResponse)
async def upload_and_analyze(
    company_id: int,
    model_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Validate model
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model.status != "completed":
        raise HTTPException(status_code=400, detail="Model is not ready for inference")

    # Save uploaded image
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    analysis_dir = os.path.join(upload_dir, "analysis_images")
    os.makedirs(analysis_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1]
    filename = f"analysis_{company_id}_{model_id}_{int(time.time())}{file_ext}"
    file_path = os.path.join(analysis_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Start analysis task
    task = analyze_image_task.delay(company_id, model_id, file_path)

    return AnalysisResponse(
        task_id=task.id,
        message="Analysis started successfully"
    )


# Get Analysis Status
@router.get("/status/{task_id}")
def get_analysis_status(task_id: str):
    task = celery_app.AsyncResult(task_id)

    response = {
        'task_id': task_id,
        'state': task.state,
        'status': None,
        'result': None
    }

    if task.state == 'PENDING':
        response['status'] = 'Analysis is waiting to start'
    elif task.state == 'STARTED':
        response['status'] = 'Analysis has started'
    elif task.state == 'PROGRESS':
        response['status'] = str(task.info.get('status', ''))
    elif task.state == 'SUCCESS':
        response['status'] = 'Analysis completed successfully'
        response['result'] = task.result
    elif task.state == 'FAILURE':
        response['status'] = f'Analysis failed: {str(task.info)}'
    
    return response


# Get Company Analyses
@router.get("/company/{company_id}", response_model=List[AnalysisResultResponse])
def get_company_analyses(company_id: int, limit: int = 50, db: Session = Depends(get_db)):
    analyses = db.query(Analysis).filter(
        Analysis.company_id == company_id
    ).order_by(Analysis.analysis_date.desc()).limit(limit).all()

    return analyses


# Get Analysis by ID
@router.get("/{analysis_id}", response_model=AnalysisResultResponse)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


# ============================================================================
# GELİŞMİŞ ANALİZ (DİNAMİK MODEL YÜKLEME)
# ============================================================================

@router.post("/analyze")
async def enhanced_analyze(
    file: UploadFile = File(...),
    eye_count: int = 3,
    shelf_id: Optional[str] = None,
    company_id: Optional[int] = 1,
    save_to_db: bool = True,
    db: Session = Depends(get_db)
):
    """
    Gelişmiş Raf Analizi
    - ROI (Raf Gözü) bazlı analiz
    - Klasik CV + YOLO hibrit yaklaşım
    - Zaman serisi karşılaştırma
    - Şirket bazlı özel model desteği
    """
    start_time = time.time()
    
    try:
        # Kalıcı klasör oluştur
        upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        analysis_dir = os.path.join(upload_dir, "analysis_images")
        os.makedirs(analysis_dir, exist_ok=True)

        # Dosyayı kalıcı olarak kaydet
        file_ext = os.path.splitext(file.filename)[1]
        timestamp = int(time.time())
        filename = f"analysis_{company_id}_{shelf_id or 'unknown'}_{timestamp}{file_ext}"
        file_path = os.path.join(analysis_dir, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            from ultralytics import YOLO
            import cv2
            from app.ai.shelf_analyzer import ShelfAnalyzer

            # Görüntüyü oku
            img = cv2.imread(file_path)
            if img is None:
                raise Exception("Görüntü okunamadı")

            # ŞİRKETİN AKTİF MODELİNİ YÜK
            model_path, model_record = get_company_model(company_id, db)
            
            detections = []
            model_info = {
                'model_path': model_path,
                'model_id': model_record.id if model_record else None,
                'model_name': model_record.name if model_record else 'Default YOLO',
                'model_version': model_record.version if model_record else 'yolov8n'
            }
            
            try:
                model = YOLO(model_path)
                results = model(img)
                
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])

                        detections.append({
                            "class": model.names[cls],
                            "confidence": conf,
                            "x": int((x1 + x2) / 2),
                            "y": int((y1 + y2) / 2),
                            "bbox": {
                                "x1": int(x1),
                                "y1": int(y1),
                                "x2": int(x2),
                                "y2": int(y2)
                            }
                        })
                        
            except Exception as model_error:
                print(f"⚠️ Model hatası: {model_error}")
                # Fallback: Varsayılan modele geç
                if model_path != 'yolov8n.pt':
                    print("🔄 Varsayılan modele geçiliyor...")
                    try:
                        model = YOLO('yolov8n.pt')
                        model_info['model_path'] = 'yolov8n.pt (fallback)'
                        model_info['model_name'] = 'Default YOLO (Fallback)'
                        
                        results = model(img)
                        for r in results:
                            boxes = r.boxes
                            for box in boxes:
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                conf = float(box.conf[0])
                                cls = int(box.cls[0])
                                detections.append({
                                    "class": model.names[cls],
                                    "confidence": conf,
                                    "x": int((x1 + x2) / 2),
                                    "y": int((y1 + y2) / 2),
                                    "bbox": {
                                        "x1": int(x1),
                                        "y1": int(y1),
                                        "x2": int(x2),
                                        "y2": int(y2)
                                    }
                                })
                    except:
                        detections = []

            # Gelişmiş analiz
            analyzer = ShelfAnalyzer(img.shape, eye_count=eye_count)
            analysis_result = analyzer.analyze_shelf(detections, img)
            
            # Model bilgisini ekle
            analysis_result['model_info'] = model_info

            # Zaman serisi karşılaştırması
            comparison = None
            if shelf_id and save_to_db:
                prev_analyses = db.query(Analysis).filter(
                    Analysis.company_id == company_id,
                    Analysis.image_path.contains(shelf_id)
                ).order_by(Analysis.analysis_date.desc()).limit(1).all()

                if prev_analyses:
                    prev_analysis = prev_analyses[0]
                    if prev_analysis.detections:
                        try:
                            prev_data = prev_analysis.detections if isinstance(prev_analysis.detections, dict) else json.loads(prev_analysis.detections)
                            comparison = ShelfAnalyzer.compare_analyses(prev_data, analysis_result)
                        except Exception as comp_error:
                            print(f"⚠️ Karşılaştırma hatası: {comp_error}")

            # Inference süresi
            inference_time = time.time() - start_time

            # VERİTABANINA KAYDET
            analysis_id = None
            if save_to_db:
                try:
                    new_analysis = Analysis(
                        company_id=company_id,
                        model_id=model_record.id if model_record else 1,
                        image_path=file_path,
                        detections=analysis_result,
                        total_products=analysis_result['summary']['total_products'],
                        product_counts=analysis_result['summary']['product_counts'],
                        shelf_coverage=analysis_result['summary']['shelf_coverage'],
                        visibility_score=analysis_result['summary']['visibility_score'],
                        total_score=analysis_result['summary']['total_score'],
                        planogram_score=0.0,
                        inference_time=inference_time
                    )
                    
                    db.add(new_analysis)
                    db.commit()
                    db.refresh(new_analysis)
                    
                    analysis_id = new_analysis.id
                    print(f"✅ Analiz kaydedildi (ID: {analysis_id})")
                    
                except Exception as db_error:
                    print(f"⚠️ Veritabanı hatası: {db_error}")
                    db.rollback()

            # Sonuç hazırla
            response = {
                "success": True,
                "analysis_id": analysis_id,
                "analysis": analysis_result,
                "model_used": model_info,
                "inference_time": round(inference_time, 2),
                "saved_to_db": save_to_db and analysis_id is not None,
                "message": f"{analysis_result['summary']['total_products']} ürün tespit edildi"
            }

            if comparison:
                response['comparison'] = comparison
                response['message'] += f" | Trend: {comparison['trend']}"
                
                if comparison['degraded_eyes']:
                    degraded_names = [e['eye_name'] for e in comparison['degraded_eyes']]
                    response['message'] += f" | ⚠️ Bozulan: {', '.join(degraded_names)}"

            return response

        except ImportError as e:
            return {
                "success": False,
                "error": f"Kütüphane hatası: {str(e)}",
                "total_objects": 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Analiz hatası: {str(e)}",
                "total_objects": 0
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya hatası: {str(e)}")


# ============================================================================
# MODEL YÖNETİMİ
# ============================================================================

@router.get("/models/{company_id}")
def get_company_models(company_id: int, db: Session = Depends(get_db)):
    """
    Şirketin tüm modellerini listele
    """
    models = db.query(Model).filter(
        Model.company_id == company_id
    ).order_by(Model.created_at.desc()).all()
    
    return [
        {
            'id': m.id,
            'name': m.name,
            'version': m.version,
            'status': m.status,
            'is_active': m.is_active,
            'model_path': m.model_path,
            'accuracy': m.accuracy,
            'precision': m.precision,
            'recall': m.recall,
            'mAP50': m.mAP50,
            'mAP50_95': m.mAP50_95,
            'created_at': str(m.created_at) if m.created_at else None,
            'training_completed_at': str(m.training_completed_at) if m.training_completed_at else None
        }
        for m in models
    ]


@router.post("/models/{model_id}/activate")
def activate_model(model_id: int, company_id: int, db: Session = Depends(get_db)):
    """
    Belirli bir modeli aktif yap (diğerleri pasif olur)
    """
    # Önce tüm modelleri pasif yap
    db.query(Model).filter(
        Model.company_id == company_id
    ).update({'is_active': False})
    
    # Seçili modeli aktif yap
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.company_id == company_id
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model bulunamadı")
    
    model.is_active = True
    db.commit()
    
    return {
        'success': True,
        'message': f'{model.name} aktif hale getirildi',
        'model_id': model_id,
        'model_path': model.model_path
    }


# ============================================================================
# ZAMAN SERİSİ
# ============================================================================

@router.get("/history/{shelf_id}")
def get_shelf_history(shelf_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """
    Belirli bir rafın analiz geçmişi
    """
    analyses = db.query(Analysis).filter(
        Analysis.image_path.contains(shelf_id)
    ).order_by(Analysis.analysis_date.desc()).limit(limit).all()

    history = []
    for a in analyses:
        history.append({
            'id': a.id,
            'date': str(a.analysis_date),
            'total_score': a.total_score,
            'total_products': a.total_products,
            'shelf_coverage': a.shelf_coverage
        })

    return {
        'shelf_id': shelf_id,
        'total_analyses': len(history),
        'history': history
    }