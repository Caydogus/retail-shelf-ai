import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const productAPI = {
  createProduct: async (productData) => {
    const formData = new FormData();
    formData.append('name', productData.name);
    formData.append('brand', productData.brand);
    formData.append('category', productData.category);
    formData.append('is_own_product', productData.isOwnProduct);
    if (productData.referenceImage) {
      formData.append('reference_image', productData.referenceImage);
    }
    
    const response = await axios.post(API_BASE_URL + '/products', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  getProducts: async (companyId) => {
    const response = await api.get('/products', { params: { company_id: companyId } });
    return response.data;
  },
};

export default api;
