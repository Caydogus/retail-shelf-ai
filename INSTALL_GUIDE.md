# Installation Guide

## Windows Kurulum Rehberi

### 1. Gerekli Yazılımlar

#### Python 3.11
1. https://www.python.org/downloads/ adresinden Python 3.11+ indirin
2. Kurulum sırasında "Add Python to PATH" seçeneğini işaretleyin
3. Kurulum sonrası test: \python --version\

#### Node.js 18
1. https://nodejs.org/ adresinden LTS versiyonu indirin
2. Kurulum yapın
3. Test: \
ode --version\ ve \
pm --version\

#### SQL Server
1. SQL Server 2019+ kurulu olmalı
2. SQL Server Management Studio (SSMS) önerilir
3. TCP/IP protokolünü aktif edin:
   - SQL Server Configuration Manager
   - SQL Server Network Configuration
   - Protocols for MSSQLSERVER
   - TCP/IP -> Enable

4. Veritabanı oluşturun:
\\\sql
CREATE DATABASE FotoAnaliz;
\\\

#### Redis
**Docker ile (Önerilen):**
\\\powershell
docker run -d -p 6379:6379 --name redis redis:7-alpine
\\\

**Windows için:**
1. https://github.com/microsoftarchive/redis/releases adresinden indirin
2. redis-server.exe çalıştırın

#### Git
1. https://git-scm.com/ adresinden indirin
2. Kurulum yapın

### 2. Proje Kurulumu

#### Projeyi Klonlayın
\\\powershell
git clone <repository-url>
cd retail-shelf-ai
\\\

#### Backend Kurulumu
\\\powershell
cd backend

# Virtual environment oluştur
python -m venv venv

# Aktif et
.\venv\Scripts\Activate.ps1

# Bağımlılıkları yükle
pip install -r requirements.txt
\\\

**Not**: CUDA desteği için:
\\\powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
\\\

#### .env Dosyasını Yapılandırın
\\\powershell
# backend/.env dosyasını düzenleyin
MSSQL_SERVER=localhost\\SQLEXPRESS  # Veya sizin instance adınız
MSSQL_DATABASE=FotoAnaliz
MSSQL_USERNAME=sa
MSSQL_PASSWORD=your_password
MSSQL_PORT=1433
\\\

#### Database Tabloları Oluşturun
\\\powershell
python test_db.py
\\\

Başarılı olursa "✓ All tables created successfully!" mesajı görmelisiniz.

#### Frontend Kurulumu
\\\powershell
cd frontend
npm install
\\\

### 3. Çalıştırma

#### Terminal 1: Redis
\\\powershell
# Docker ile
docker start redis

# Veya Redis executable çalıştırın
redis-server
\\\

#### Terminal 2: Backend API
\\\powershell
cd backend
.\venv\Scripts\Activate.ps1
python run.py
\\\

API: http://localhost:8000
Swagger Docs: http://localhost:8000/docs

#### Terminal 3: Celery Worker
\\\powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A app.tasks.training_tasks worker --loglevel=info
\\\

#### Terminal 4: Frontend
\\\powershell
cd frontend
npm run dev
\\\

UI: http://localhost:3000

### 4. İlk Test

1. Tarayıcıda http://localhost:3000 açın
2. "Add Company" butonuna tıklayın
3. Şirket adı girin ve kaydedin
4. Şirketi seçin
5. Products, Datasets vb. menüleri gezin

### 5. Sorun Giderme

#### ODBC Driver Hatası
\\\
Error: Can't connect to SQL Server
\\\

**Çözüm**: ODBC Driver 18 kurun
1. https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
2. İndirin ve kurun
3. Backend'i yeniden başlatın

#### Port Zaten Kullanımda
\\\
Error: Address already in use
\\\

**Çözüm**:
\\\powershell
# Port kullanan process'i bul
netstat -ano | findstr :8000

# Process'i kapat
taskkill /PID <process_id> /F
\\\

#### Redis Bağlanamıyor
\\\
Error: Error 10061 connecting to localhost:6379
\\\

**Çözüm**:
\\\powershell
# Redis çalışıyor mu kontrol et
redis-cli ping
# PONG döndürmeli

# Çalışmıyorsa başlat
docker start redis
# veya
redis-server
\\\

#### Import Hataları
\\\
Error: No module named 'app'
\\\

**Çözüm**:
\\\powershell
# Virtual environment aktif mi kontrol et
# Prompt başında (venv) yazmalı

# Tekrar aktif et
.\venv\Scripts\Activate.ps1

# Eksik paketi yükle
pip install <package_name>
\\\

### 6. Production Deployment

#### Docker Compose ile
\\\ash
# .env dosyasını ayarlayın
cp backend/.env.example backend/.env
# Düzenleyin

# Build ve başlat
docker-compose up -d

# Logları izle
docker-compose logs -f

# Durdur
docker-compose down
\\\

#### Manuel Production
1. HTTPS kullanın (nginx/Apache)
2. Environment variables ayarlayın
3. SECRET_KEY değiştirin
4. DEBUG=False
5. ALLOWED_ORIGINS sınırlayın
6. Database backup planlayın
7. Monitoring ekleyin (Prometheus, Grafana)

## Linux/Mac Kurulum

### Gereksinimler
\\\ash
# Python 3.11
sudo apt install python3.11 python3.11-venv

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Redis
sudo apt install redis-server
sudo systemctl start redis

# Git
sudo apt install git
\\\

### Kurulum
\\\ash
git clone <repository-url>
cd retail-shelf-ai

# Backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database test
python test_db.py

# Frontend
cd ../frontend
npm install
\\\

### Çalıştırma
\\\ash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python run.py

# Terminal 2: Celery
cd backend
source venv/bin/activate
celery -A app.tasks.training_tasks worker --loglevel=info

# Terminal 3: Frontend
cd frontend
npm run dev
\\\

## GPU Desteği (CUDA)

### Requirements
- NVIDIA GPU (RTX series önerilir)
- CUDA 11.8+
- cuDNN 8.6+

### Kurulum
1. CUDA Toolkit: https://developer.nvidia.com/cuda-downloads
2. cuDNN: https://developer.nvidia.com/cudnn
3. PyTorch GPU version:
\\\ash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
\\\

### Test
\\\python
import torch
print(torch.cuda.is_available())  # True olmalı
print(torch.cuda.get_device_name(0))
\\\

---

Kurulum sorunları için issue açabilirsiniz.
