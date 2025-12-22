import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [page, setPage] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [products, setProducts] = useState([]);
  const [menuOpen, setMenuOpen] = useState(false);
  const [shelfId, setShelfId] = useState('raf_a1');
  const [eyeCount, setEyeCount] = useState(3);
  const [models, setModels] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [uploadFiles, setUploadFiles] = useState([]);

  const API_URL = 'http://localhost:8000';

  useEffect(() => {
    if (page === 'dashboard') fetchStats();
    if (page === 'products') fetchProducts();
    if (page === 'training') {
      fetchModels();
      fetchDatasets();
    }
  }, [page]);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('İstatistik hatası:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/products`);
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      }
    } catch (err) {
      setError('Ürünler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchModels = async () => {
    try {
      const response = await fetch(`${API_URL}/api/analysis/models/1`);
      if (response.ok) {
        const data = await response.json();
        setModels(data);
      }
    } catch (err) {
      console.error('Model listesi hatası:', err);
    }
  };

  const fetchDatasets = async () => {
    try {
      const response = await fetch(`${API_URL}/api/datasets/company/1`);
      if (response.ok) {
        const data = await response.json();
        setDatasets(data);
      }
    } catch (err) {
      console.error('Dataset listesi hatası:', err);
    }
  };

  const handleModelActivate = async (modelId) => {
    try {
      const response = await fetch(`${API_URL}/api/analysis/models/${modelId}/activate?company_id=1`, {
        method: 'POST'
      });
      if (response.ok) {
        alert('Model aktif edildi!');
        fetchModels();
      }
    } catch (err) {
      alert('Hata: ' + err.message);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setUploadFiles(files);
  };

  const handleDatasetUpload = async () => {
    if (uploadFiles.length === 0) {
      alert('Lütfen fotoğraf seçin');
      return;
    }

    try {
      setLoading(true);
      const formData = new FormData();
      
      uploadFiles.forEach(file => {
        formData.append('files', file);
      });
      
      formData.append('dataset_name', 'Doğuş Çay Dataset');
      formData.append('company_id', '1');

      const response = await fetch(`${API_URL}/api/datasets/upload`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        alert('Dataset yüklendi!');
        setUploadFiles([]);
        fetchDatasets();
      } else {
        alert('Yükleme başarısız');
      }
    } catch (err) {
      alert('Hata: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setUploadedImage(reader.result);
      reader.readAsDataURL(file);
      setAnalysisResult(null);
    }
  };

  const analyzeImage = async () => {
    if (!uploadedImage) return;
    try {
      setLoading(true);
      setError(null);
      const formData = new FormData();
      const blob = await fetch(uploadedImage).then(r => r.blob());
      formData.append('file', blob, 'image.jpg');
      
      const url = `${API_URL}/api/analyze?eye_count=${eyeCount}&shelf_id=${shelfId}&company_id=1&save_to_db=true`;
      const response = await fetch(url, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        setAnalysisResult(data);
      } else {
        setError('Analiz başarısız oldu');
      }
    } catch (err) {
      setError('Hata: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderDashboard = () => (
    <div>
      <h1>Kontrol Paneli</h1>
      {loading ? <div className="spinner"></div> : (
        <div className="grid">
          <div className="card">
            <div className="card-label">Toplam Ürün</div>
            <div className="card-value">{stats?.total_products || 0}</div>
          </div>
          <div className="card">
            <div className="card-label">Aktif Raflar</div>
            <div className="card-value">{stats?.active_shelves || 0}</div>
          </div>
          <div className="card">
            <div className="card-label">Stok Seviyesi</div>
            <div className="card-value">{stats?.stock_level || 85}%</div>
            <div className="progress-bar">
              <div className="progress-fill" style={{width: `${stats?.stock_level || 85}%`}}></div>
            </div>
          </div>
          <div className="card">
            <div className="card-label">Uyarılar</div>
            <div className="card-value">{stats?.alerts || 3}</div>
            <span className="badge warning">Düşük Stok</span>
          </div>
          <div className="card full-width">
            <h3>Son Aktiviteler</h3>
            <div className="alert success">✓ A1 rafı yenilendi - 2 saat önce</div>
            <div className="alert warning">⚠ B3 rafında düşük stok - 4 saat önce</div>
          </div>
        </div>
      )}
    </div>
  );

  const renderAnalysis = () => (
    <div>
      <h1>Görüntü Analizi (YOLOv8 + Klasik CV)</h1>
      <div className="card">
        <div className="analysis-settings">
          <div className="setting-group">
            <label>Raf ID (Zaman Serisi İçin)</label>
            <input 
              type="text" 
              value={shelfId} 
              onChange={(e) => setShelfId(e.target.value)}
              placeholder="raf_a1"
            />
          </div>
          <div className="setting-group">
            <label>Raf Gözü Sayısı</label>
            <input 
              type="number" 
              value={eyeCount} 
              onChange={(e) => setEyeCount(parseInt(e.target.value))}
              min="2"
              max="6"
            />
          </div>
        </div>

        <label className="btn btn-primary upload-btn">
          📷 Raf Görüntüsü Yükle
          <input type="file" hidden accept="image/*" onChange={handleImageUpload} />
        </label>
        
        {uploadedImage && (
          <div className="upload-preview">
            <img src={uploadedImage} alt="Yüklenen" className="preview-image" />
            <button 
              className="btn btn-primary" 
              onClick={analyzeImage} 
              disabled={loading}
            >
              {loading ? 'Analiz Ediliyor...' : '🔍 Analiz Et'}
            </button>
          </div>
        )}
        
        {error && <div className="alert error">{error}</div>}
        
        {analysisResult && analysisResult.success && (
          <div className="results">
            <h3>Analiz Sonuçları</h3>
            
            {/* Zaman Serisi Karşılaştırma */}
            {analysisResult.comparison && (
              <div className={`alert ${analysisResult.comparison.trend === 'stable' ? 'info' : analysisResult.comparison.trend === 'improving' ? 'success' : 'warning'}`}>
                <strong>Trend:</strong> {analysisResult.comparison.trend === 'stable' ? '📊 Sabit' : analysisResult.comparison.trend === 'improving' ? '📈 İyileşiyor' : '📉 Kötüleşiyor'}
                <span style={{marginLeft: '1rem'}}>
                  Delta: {analysisResult.comparison.total_score_delta > 0 ? '+' : ''}{analysisResult.comparison.total_score_delta}
                </span>
                {analysisResult.comparison.degraded_eyes.length > 0 && (
                  <div style={{marginTop: '0.5rem'}}>
                    ⚠️ Bozulan Gözler: {analysisResult.comparison.degraded_eyes.map(e => e.eye_name).join(', ')}
                  </div>
                )}
              </div>
            )}

            {/* Genel Özet */}
            <div className="grid">
              <div className="card">
                <div className="card-label">Toplam Skor</div>
                <div className="card-value">{analysisResult.analysis.summary.total_score}</div>
              </div>
              <div className="card">
                <div className="card-label">Tespit Edilen Ürün</div>
                <div className="card-value">{analysisResult.analysis.summary.total_products}</div>
              </div>
              <div className="card">
                <div className="card-label">Raf Kaplaması</div>
                <div className="card-value">{analysisResult.analysis.summary.shelf_coverage}%</div>
              </div>
              <div className="card">
                <div className="card-label">İnceleme Süresi</div>
                <div className="card-value">{analysisResult.inference_time}s</div>
              </div>
            </div>

            {/* Raf Gözü Detayları */}
            <h3 style={{marginTop: '2rem'}}>Raf Gözleri Analizi</h3>
            <div className="eyes-container">
              {analysisResult.analysis.eyes.map((eye) => (
                <div key={eye.eye_id} className="eye-card">
                  <h4>{eye.eye_name}</h4>
                  <div className="eye-score">
                    <span className="score-label">Hibrit Skor:</span>
                    <span className="score-value">{eye.hybrid_score}</span>
                  </div>
                  
                  <div className="metrics">
                    <div className="metric">
                      <span>Ürün Sayısı:</span>
                      <strong>{eye.total_products}</strong>
                    </div>
                    <div className="metric">
                      <span>Kaplama:</span>
                      <strong>{eye.coverage}%</strong>
                    </div>
                  </div>

                  {eye.classic_metrics && (
                    <details className="classic-metrics">
                      <summary>Klasik CV Metrikleri</summary>
                      <div className="metrics-grid">
                        <div className="metric-item">
                          <span>Kenar Yoğunluğu</span>
                          <strong>{eye.classic_metrics.edge_density}</strong>
                        </div>
                        <div className="metric-item">
                          <span>Doku Varyansı</span>
                          <strong>{eye.classic_metrics.texture_variance.toFixed(0)}</strong>
                        </div>
                        <div className="metric-item">
                          <span>Parlaklık</span>
                          <strong>{eye.classic_metrics.luminance.toFixed(0)}</strong>
                        </div>
                        <div className="metric-item">
                          <span>Tahmini Doluluk</span>
                          <strong>{eye.classic_metrics.estimated_fullness}%</strong>
                        </div>
                      </div>
                    </details>
                  )}
                </div>
              ))}
            </div>

            {analysisResult.saved_to_db && (
              <div className="alert success" style={{marginTop: '1rem'}}>
                ✅ Analiz veritabanına kaydedildi (ID: {analysisResult.analysis_id})
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );

  const renderProducts = () => (
    <div>
      <h1>Ürünler</h1>
      {loading ? <div className="spinner"></div> : (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Ürün Adı</th>
              <th>Kategori</th>
              <th>Stok</th>
              <th>Durum</th>
            </tr>
          </thead>
          <tbody>
            {products.length > 0 ? (
              products.map(p => (
                <tr key={p.id}>
                  <td>{p.id}</td>
                  <td>{p.name}</td>
                  <td>{p.category}</td>
                  <td>{p.stock}</td>
                  <td>
                    <span className={`badge ${p.stock > 10 ? 'success' : 'warning'}`}>
                      {p.stock > 10 ? 'Stokta' : 'Düşük Stok'}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" style={{textAlign: 'center'}}>
                  Ürün bulunamadı. MSSQL veritabanınızı bağlayın.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );

  const renderShelves = () => (
    <div>
      <h1>Raf Yönetimi</h1>
      <div className="grid">
        {['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map(shelf => (
          <div className="card" key={shelf}>
            <h3>Raf {shelf}</h3>
            <p>Kapasite: %85</p>
            <div className="progress-bar">
              <div className="progress-fill" style={{width: '85%'}}></div>
            </div>
            <button className="btn btn-outline">Detayları Gör</button>
          </div>
        ))}
      </div>
    </div>
  );

  const renderReports = () => (
    <div>
      <h1>Raporlar ve Analizler</h1>
      <div className="card">
        <h3>Stok Analizi</h3>
        <div className="alert info">
          📊 Raporlar özelliği yakında gelecek. Stok trendleri, raf performansı ve daha fazlası.
        </div>
      </div>
    </div>
  );

  const renderTraining = () => (
    <div>
      <h1>Model Eğitimi</h1>
      
      {/* Dataset Upload */}
      <div className="card">
        <h3>📸 Dataset Yükle</h3>
        <p>Eğitim için raf fotoğraflarını yükleyin (50-200 adet önerilir)</p>
        
        <input 
          type="file" 
          multiple 
          accept="image/*"
          onChange={handleFileSelect}
          style={{marginBottom: '1rem'}}
        />
        
        {uploadFiles.length > 0 && (
          <div className="alert info">
            {uploadFiles.length} dosya seçildi
          </div>
        )}
        
        <button 
          className="btn btn-primary" 
          onClick={handleDatasetUpload}
          disabled={loading || uploadFiles.length === 0}
        >
          {loading ? 'Yükleniyor...' : '⬆️ Dataset Yükle'}
        </button>
      </div>

      {/* Mevcut Datasets */}
      <div className="card" style={{marginTop: '2rem'}}>
        <h3>📁 Mevcut Dataset'ler</h3>
        {datasets.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>İsim</th>
                <th>Fotoğraf Sayısı</th>
                <th>Durum</th>
                <th>Tarih</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map(d => (
                <tr key={d.id}>
                  <td>{d.id}</td>
                  <td>{d.name}</td>
                  <td>{d.image_count || 0}</td>
                  <td>
                    <span className={`badge ${d.status === 'ready' ? 'success' : 'warning'}`}>
                      {d.status}
                    </span>
                  </td>
                  <td>{d.created_at ? new Date(d.created_at).toLocaleDateString('tr-TR') : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="alert info">
            Henüz dataset yüklenmemiş. Yukarıdan fotoğrafları yükleyin.
          </div>
        )}
      </div>

      {/* Mevcut Modeller */}
      <div className="card" style={{marginTop: '2rem'}}>
        <h3>🤖 Mevcut Modeller</h3>
        {models.length > 0 ? (
          <div className="grid">
            {models.map(m => (
              <div key={m.id} className={`eye-card ${m.is_active ? 'active-model' : ''}`}>
                <h4>{m.name}</h4>
                <div className="metrics">
                  <div className="metric">
                    <span>Versiyon:</span>
                    <strong>{m.version}</strong>
                  </div>
                  <div className="metric">
                    <span>Durum:</span>
                    <span className={`badge ${m.status === 'completed' ? 'success' : 'warning'}`}>
                      {m.status}
                    </span>
                  </div>
                  {m.mAP50 && (
                    <div className="metric">
                      <span>mAP50:</span>
                      <strong>{m.mAP50}%</strong>
                    </div>
                  )}
                  <div className="metric">
                    <span>Aktif:</span>
                    <strong>{m.is_active ? '✅ Evet' : '❌ Hayır'}</strong>
                  </div>
                </div>
                
                {!m.is_active && m.status === 'completed' && (
                  <button 
                    className="btn btn-outline" 
                    style={{marginTop: '1rem'}}
                    onClick={() => handleModelActivate(m.id)}
                  >
                    🔄 Aktif Et
                  </button>
                )}
                
                {m.is_active && (
                  <div className="alert success" style={{marginTop: '1rem', padding: '0.5rem'}}>
                    ✅ Aktif Model
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="alert info">
            Model bulunamadı.
          </div>
        )}
      </div>

      {/* Training Start (Gelecek) */}
      <div className="card" style={{marginTop: '2rem'}}>
        <h3>🎓 Model Eğitimi Başlat</h3>
        <div className="alert warning">
          ⚠️ Model eğitimi özelliği yakında aktif olacak. Dataset yüklendikten sonra burada eğitim başlatabileceksiniz.
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (page) {
      case 'dashboard': return renderDashboard();
      case 'analyze': return renderAnalysis();
      case 'products': return renderProducts();
      case 'shelves': return renderShelves();
      case 'reports': return renderReports();
      case 'training': return renderTraining();
      default: return renderDashboard();
    }
  };

  return (
    <div className="app">
      <header className="header">
        <button className="menu-btn" onClick={() => setMenuOpen(!menuOpen)}>☰</button>
        <h1>Retail Shelf AI - ROI Analiz Sistemi</h1>
        <span className="badge success">Backend: Aktif</span>
      </header>
      
      <div className="layout">
        <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
          <nav>
            <button onClick={() => { setPage('dashboard'); setMenuOpen(false); }} className={page === 'dashboard' ? 'active' : ''}>
              📊 Kontrol Paneli
            </button>
            <button onClick={() => { setPage('analyze'); setMenuOpen(false); }} className={page === 'analyze' ? 'active' : ''}>
              📷 Görüntü Analizi
            </button>
            <button onClick={() => { setPage('products'); setMenuOpen(false); }} className={page === 'products' ? 'active' : ''}>
              📦 Ürünler
            </button>
            <button onClick={() => { setPage('shelves'); setMenuOpen(false); }} className={page === 'shelves' ? 'active' : ''}>
              🏪 Raflar
            </button>
            <button onClick={() => { setPage('reports'); setMenuOpen(false); }} className={page === 'reports' ? 'active' : ''}>
              📈 Raporlar
            </button>
            <button onClick={() => { setPage('training'); setMenuOpen(false); }} className={page === 'training' ? 'active' : ''}>
              🎓 Model Eğitimi
            </button>
          </nav>
        </aside>
        
        <main className="content">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App;