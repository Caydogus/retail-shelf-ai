# Retail Shelf AI - Raf Analiz ve Ürün Tespit Sistemi

Yapay zeka destekli perakende raf analizi ve ürün tespit sistemi. YOLOv8 tabanlı nesne tespiti, raf analizi, renk analizi ve puanlama motoru içerir.

## 🚀 Özellikler

### Backend (FastAPI + Python)
- ✅ **Şirket Yönetimi**: Çoklu şirket desteği
- ✅ **Ürün Kataloğu**: Ürün yönetimi, görseller, referans renkler
- ✅ **Dataset Yönetimi**: YOLO format, annotation, train/val split
- ✅ **YOLOv8 Eğitimi**: Otomatik model eğitimi (Celery ile async)
- ✅ **Raf Analizi**: Tespit, doluluk oranı, dağılım analizi
- ✅ **Renk Analizi**: Dominant renk tespiti, karşılaştırma
- ✅ **Puanlama Motoru**: Özelleştirilebilir skorlama kuralları
- ✅ **Raporlama**: Detaylı analiz ve eğitim raporları

### Frontend (React + Vite + Material-UI)
- ✅ **Dashboard**: Şirket yönetimi ve genel bakış
- ✅ **Ürün Yönetimi**: Katalog ve görseller
- ✅ **Dataset Oluşturma**: Upload, annotation tool
- ✅ **Model Eğitimi**: Progress tracking
- ✅ **Analiz Arayüzü**: Görüntü yükleme ve sonuç görüntüleme
- ✅ **Puanlama Kuralları**: Kural yönetimi

## 📋 Gereksinimler

### Backend
- Python 3.11+
- SQL Server 2019+
- Redis 7+
- CUDA (opsiyonel, GPU için)

### Frontend
- Node.js 18+
- npm 9+

## 🛠️ Kurulum

### 1. Repository'yi Klonlayın
\\\ash
git clone <repository-url>
cd retail-shelf-ai
\\\

### 2. Backend Kurulumu

\\\powershell
cd backend

# Virtual environment oluştur
python -m venv venv
.\venv\Scripts\Activate.ps1

# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyasını düzenle (MSSQL bağlantı bilgileri)
# MSSQL_SERVER=your_server
# MSSQL_DATABASE=FotoAnaliz
# MSSQL_USERNAME=sa
# MSSQL_PASSWORD=your_password
\\\

### 3. Database Oluşturma

\\\powershell
# Test ve tablo oluşturma
python test_db.py
\\\

### 4. Redis Başlatma

\\\powershell
# Docker ile
docker run -d -p 6379:6379 redis:7-alpine

# Veya Windows için Redis indirin
\\\

### 5. Frontend Kurulumu

\\\powershell
cd frontend

# Bağımlılıkları yükle
npm install
\\\

## 🚀 Çalıştırma

### Otomatik Başlatma (Önerilen)

#### Backend
\\\powershell
cd backend
.\start_dev.ps1
\\\

#### Celery Worker (Ayrı terminal)
\\\powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A app.tasks.training_tasks worker --loglevel=info
\\\

#### Frontend
\\\powershell
cd frontend
npm run dev
\\\

### Manuel Başlatma

#### Backend API
\\\powershell
cd backend
python run.py
\\\

API: http://localhost:8000
Docs: http://localhost:8000/docs

#### Frontend
\\\powershell
cd frontend
npm run dev
\\\

UI: http://localhost:3000

## 🐳 Docker ile Çalıştırma

\\\ash
# Tüm servisleri başlat
docker-compose up -d

# Logları izle
docker-compose logs -f

# Durdur
docker-compose down
\\\

## 📚 API Endpoints

### Companies
- \POST /api/companies/\ - Şirket oluştur
- \GET /api/companies/\ - Şirketleri listele
- \GET /api/companies/{id}\ - Şirket detayı
- \PUT /api/companies/{id}\ - Şirket güncelle
- \DELETE /api/companies/{id}\ - Şirket sil
- \POST /api/companies/{id}/logo\ - Logo yükle

### Products
- \POST /api/products/\ - Ürün oluştur
- \GET /api/products/company/{id}\ - Şirket ürünleri
- \GET /api/products/{id}\ - Ürün detayı
- \PUT /api/products/{id}\ - Ürün güncelle
- \DELETE /api/products/{id}\ - Ürün sil
- \POST /api/products/{id}/image\ - Ürün görseli yükle

### Datasets
- \POST /api/datasets/\ - Dataset oluştur
- \POST /api/datasets/{id}/upload-image\ - Görüntü yükle
- \POST /api/datasets/{id}/annotate/{file}\ - Annotation ekle
- \POST /api/datasets/{id}/prepare\ - Dataset hazırla (train/val split + YAML)
- \GET /api/datasets/{id}/stats\ - İstatistikler
- \GET /api/datasets/{id}/validate\ - Validasyon

### Training
- \POST /api/training/start\ - Eğitimi başlat (async)
- \GET /api/training/status/{task_id}\ - Task durumu
- \GET /api/training/history/company/{id}\ - Eğitim geçmişi

### Analysis
- \POST /api/analysis/upload\ - Görüntü analizi başlat (async)
- \GET /api/analysis/status/{task_id}\ - Analiz durumu
- \GET /api/analysis/company/{id}\ - Şirket analizleri
- \GET /api/analysis/{id}\ - Analiz detayı

### Scoring
- \POST /api/scoring/\ - Puanlama kuralı oluştur
- \GET /api/scoring/company/{id}\ - Şirket kuralları
- \POST /api/scoring/calculate\ - Skor hesapla
- \POST /api/scoring/company/{id}/calculate\ - Özel kurallarla hesapla

## 🏗️ Proje Yapısı

\\\
retail-shelf-ai/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── models/           # Database models
│   │   ├── ai/               # AI modülleri (YOLO, analiz)
│   │   ├── services/         # İş mantığı
│   │   └── tasks/            # Celery tasks
│   ├── models/               # Eğitilmiş modeller
│   ├── datasets/             # Training dataları
│   ├── uploads/              # Yüklenen dosyalar
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React bileşenleri
│   │   ├── pages/            # Sayfalar
│   │   └── services/         # API servisleri
│   └── package.json
└── docker-compose.yml
\\\

## 🔧 Teknolojiler

### Backend
- **FastAPI**: Modern, hızlı web framework
- **SQLAlchemy**: ORM
- **MSSQL Server**: Database
- **YOLOv8 (Ultralytics)**: Nesne tespiti
- **OpenCV**: Görüntü işleme
- **Celery**: Background tasks
- **Redis**: Message broker & cache
- **Scikit-learn**: Renk analizi (KMeans)

### Frontend
- **React 18**: UI framework
- **Vite**: Build tool
- **Material-UI**: Component library
- **React Router**: Navigation
- **Axios**: HTTP client
- **Recharts**: Grafikler
- **Konva**: Canvas işlemleri (annotation)

## 📊 Kullanım Akışı

### 1. Şirket Oluşturma
- Dashboard'dan "Add Company" ile yeni şirket oluştur
- Logo yükle (opsiyonel)

### 2. Ürün Kataloğu
- Şirketi seç
- Products sayfasından ürünleri ekle
- Her ürün için: isim, SKU, kategori, referans renkler
- Ürün görseli yükle

### 3. Dataset Oluşturma
- Dataset oluştur
- Raf görüntülerini yükle
- Annotation tool ile ürünleri işaretle (bounding boxes)
- "Prepare Dataset" ile train/val split yap

### 4. Model Eğitimi
- Dataset'i seç
- Eğitim parametrelerini ayarla (epochs, batch size)
- "Start Training" ile başlat
- Progress'i takip et
- Eğitim bittikten sonra metrikleri görüntüle (mAP, precision, recall)

### 5. Raf Analizi
- Eğitilmiş modeli seç
- Analiz edilecek raf görüntüsünü yükle
- Sistem otomatik olarak:
  - Ürünleri tespit eder
  - Raf doluluk oranını hesaplar
  - Ürün dağılımını analiz eder
  - Renk uyumunu kontrol eder
  - Toplam skor üretir
- Sonuçları ve önerileri görüntüle

### 6. Puanlama Kuralları
- Şirket özel puanlama kuralları oluştur
- Ağırlıkları özelleştir
- Analizlerde otomatik kullanılır

## 🧪 Test

### Backend Test
\\\powershell
cd backend

# Database bağlantısı test
python test_db.py

# API test
curl http://localhost:8000/health

# Celery test
curl http://localhost:8000/api/training/test-celery
\\\

### Frontend Test
\\\powershell
cd frontend
npm run dev

# http://localhost:3000 adresini aç
\\\

## 🐛 Sorun Giderme

### MSSQL Bağlantı Hatası
1. SQL Server çalışıyor mu kontrol edin
2. TCP/IP protokolü aktif mi?
3. .env dosyasındaki bilgiler doğru mu?
4. Firewall ayarlarını kontrol edin

### Celery Çalışmıyor
1. Redis çalışıyor mu? \edis-cli ping\
2. .env'de CELERY_BROKER_URL doğru mu?
3. Worker loglarını kontrol edin

### Model Eğitimi Başlamıyor
1. Dataset hazır mı? (status: ready)
2. YAML dosyası oluşturulmuş mu?
3. Celery worker çalışıyor mu?
4. Disk alanı yeterli mi?

### Frontend API'ye Bağlanamıyor
1. Backend çalışıyor mu? http://localhost:8000/health
2. CORS ayarları doğru mu?
3. .env'de VITE_API_URL doğru mu?

## 📈 Performans

### Önerilen Sistem Gereksinimleri
- **CPU**: 4+ cores
- **RAM**: 16GB+ (32GB önerilir)
- **GPU**: NVIDIA RTX series (CUDA 11.8+)
- **Disk**: 50GB+ SSD

### Optimizasyon
- GPU kullanımı için CUDA kurulumu
- Redis persistence ayarları
- Dataset cache mekanizması
- Model quantization (inference hızı için)

## 🔒 Güvenlik

- API key authentication (TODO)
- HTTPS kullanımı (production)
- Input validation
- SQL injection koruması (SQLAlchemy ORM)
- File upload validasyonu
- Rate limiting (TODO)

## 📝 Lisans

MIT License

## 👥 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (\git checkout -b feature/amazing\)
3. Commit edin (\git commit -m 'Add amazing feature'\)
4. Push edin (\git push origin feature/amazing\)
5. Pull Request açın

## 📧 İletişim

Sorularınız için issue açabilirsiniz.

## 🙏 Teşekkürler

- Ultralytics YOLOv8
- FastAPI
- Material-UI
- OpenCV
- Celery

---

**Not**: Bu sistem perakende raf analizi için geliştirilmiştir. Eğitim datası kalitesi sonuçları doğrudan etkiler.
