import os
from fastapi import FastAPI, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from app.api import companies, products, datasets, training, analysis, scoring
from app.models.database import get_db, Product, Analysis as AnalysisModel

# Create FastAPI app
app = FastAPI(
    title="Retail Shelf AI API",
    description="AI-powered retail shelf analysis and product detection system",
    version="1.0.0"
)

# CORS Configuration - Tüm originlere izin ver
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tüm domainlere izin
    allow_credentials=False,  # Credentials kapalı
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(training.router, prefix="/api/training", tags=["Training"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["Scoring"])


@app.get("/")
def read_root():
    return {
        "message": "Retail Shelf AI API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ============================================================================
# Frontend için kısayol endpoint'leri
# ============================================================================

@app.get("/api/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Dashboard için istatistikler
    """
    try:
        total_products = db.query(Product).count()
        total_analyses = db.query(AnalysisModel).count()
        
        # Son analizlerin ortalama skoru
        recent_analyses = db.query(AnalysisModel).order_by(
            AnalysisModel.analysis_date.desc()
        ).limit(10).all()
        
        avg_score = sum(a.total_score for a in recent_analyses) / len(recent_analyses) if recent_analyses else 85
        
        # Düşük stok uyarısı (örnek)
        alerts = 3
        
        return {
            "total_products": total_products,
            "active_shelves": 6,
            "stock_level": int(avg_score),
            "alerts": alerts
        }
    except Exception as e:
        # Veritabanı bağlantısı yoksa varsayılan değerler
        return {
            "total_products": 0,
            "active_shelves": 6,
            "stock_level": 85,
            "alerts": 3
        }


# Frontend'den direkt /api/analyze çağrısı için yönlendirme
from app.api.analysis import enhanced_analyze

@app.post("/api/analyze")
async def analyze_shortcut(
    file: UploadFile = File(...),
    eye_count: int = 3,
    db: Session = Depends(get_db)
):
    """
    Frontend için kısayol - gelişmiş ROI analizi
    """
    return await enhanced_analyze(file=file, eye_count=eye_count, db=db)