
import { useState } from 'react';
import { productAPI } from '../services/api';
import './ProductAdd.css';

function ProductAdd() {
  const [formData, setFormData] = useState({
    name: '',
    brand: '',
    category: '',
    isOwnProduct: true,
    referenceImage: null,
  });
  
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData(prev => ({ ...prev, referenceImage: file }));
      
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      if (!formData.name || !formData.brand || !formData.referenceImage) {
        setMessage({ type: 'error', text: 'Lütfen tüm alanları doldurun!' });
        setLoading(false);
        return;
      }

      await productAPI.createProduct(formData);
      
      setMessage({ type: 'success', text: 'Ürün başarıyla eklendi!' });
      
      setFormData({
        name: '',
        brand: '',
        category: '',
        isOwnProduct: true,
        referenceImage: null,
      });
      setPreview(null);
      
    } catch (error) {
      console.error('Ürün ekleme hatası:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Ürün eklenirken bir hata oluştu!' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='product-add-container'>
      <div className='product-add-card'>
        <h1>Yeni Ürün Ekle</h1>
        <p className='subtitle'>Referans ürün bilgilerini girin</p>

        {message.text && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className='form-group'>
            <label htmlFor='name'>Ürün Adı *</label>
            <input
              type='text'
              id='name'
              name='name'
              value={formData.name}
              onChange={handleInputChange}
              placeholder='Örn: Ülker Çikolatalı Gofret'
              required
            />
          </div>

          <div className='form-group'>
            <label htmlFor='brand'>Marka *</label>
            <input
              type='text'
              id='brand'
              name='brand'
              value={formData.brand}
              onChange={handleInputChange}
              placeholder='Örn: Ülker'
              required
            />
          </div>

          <div className='form-group'>
            <label htmlFor='category'>Kategori</label>
            <select
              id='category'
              name='category'
              value={formData.category}
              onChange={handleInputChange}
            >
              <option value=''>Kategori Seçin</option>
              <option value='Gofret'>Gofret</option>
              <option value='Çikolata'>Çikolata</option>
              <option value='Bisküvi'>Bisküvi</option>
              <option value='Çay'>Çay</option>
              <option value='Kahve'>Kahve</option>
              <option value='Süt'>Süt</option>
              <option value='Meyve Suyu'>Meyve Suyu</option>
              <option value='Gazlı İçecek'>Gazlı İçecek</option>
              <option value='Diğer'>Diğer</option>
            </select>
          </div>

          <div className='form-group checkbox-group'>
            <label>
              <input
                type='checkbox'
                name='isOwnProduct'
                checked={formData.isOwnProduct}
                onChange={handleInputChange}
              />
              <span>Bu bizim ürünümüz</span>
            </label>
            <small>İşaretli değilse rakip ürün olarak kaydedilir</small>
          </div>

          <div className='form-group'>
            <label htmlFor='referenceImage'>Referans Fotoğraf *</label>
            <div className='file-upload-area'>
              <input
                type='file'
                id='referenceImage'
                accept='image/*'
                onChange={handleImageChange}
                required
              />
              <div className='upload-instructions'>
                <svg width='48' height='48' viewBox='0 0 24 24' fill='none' stroke='currentColor'>
                  <path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4' strokeWidth='2' strokeLinecap='round' strokeLinejoin='round'/>
                  <polyline points='17 8 12 3 7 8' strokeWidth='2' strokeLinecap='round' strokeLinejoin='round'/>
                  <line x1='12' y1='3' x2='12' y2='15' strokeWidth='2' strokeLinecap='round' strokeLinejoin='round'/>
                </svg>
                <p>Fotoğraf yüklemek için tıklayın</p>
                <small>Ön cephe, temiz, tek ürün, sade arka plan</small>
              </div>
            </div>
          </div>

          {preview && (
            <div className='image-preview'>
              <h3>Önizleme</h3>
              <img src={preview} alt='Önizleme' />
            </div>
          )}

          <button type='submit' className='submit-btn' disabled={loading}>
            {loading ? 'Ekleniyor...' : 'Ürünü Ekle'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default ProductAdd;
