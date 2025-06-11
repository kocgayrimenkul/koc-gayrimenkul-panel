// PropertyService.js - Gayrimenkul API Servisi

import axios from 'axios';
import useSWR from 'swr';

// API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// SWR fetcher fonksiyonu
const fetcher = async (url) => {
  try {
    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    throw error;
  }
};

// Cache anahtarları
const CACHE_KEYS = {
  ALL_PROPERTIES: 'properties/all',
  PROPERTY_DETAIL: (id) => `properties/${id}`,
  PROPERTY_SEARCH: 'properties/search',
  PROPERTY_STATS: 'properties/stats',
  NEIGHBORHOODS: 'neighborhoods/all',
  FSBO_LIST: 'fsbo/all',
  PROPERTY_TYPES: 'properties/types',
  FEATURED_PROPERTIES: 'properties/featured',
};

/**
 * Gayrimenkul Servisi
 * Gayrimenkul verilerini, mahalleri ve FSBO kayıtlarını yönetmek için API wrapper
 */
class PropertyService {
  constructor() {
    console.log('🏠 [API] PropertyService başlatılıyor');
    console.log('🏠 [API] Base URL:', API_BASE_URL);
    
    this.isDebugMode = true; // Debug modu aktif
    
    this.axios = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    // İstek yapıldığında token ekleyen interceptor
    this.axios.interceptors.request.use(
      async (config) => {
        const token = await this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        if (this.isDebugMode) {
          console.log(`🏠 [API] İstek yapılıyor: ${config.method.toUpperCase()} ${config.baseURL}${config.url}`);
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Yanıt alındığında hata kontrolü yapan interceptor
    this.axios.interceptors.response.use(
      (response) => {
        if (this.isDebugMode) {
          console.log(`✅ [API] Başarılı yanıt: ${response.status} ${response.config.method.toUpperCase()} ${response.config.url}`);
        }
        return response;
      },
      async (error) => {
        if (error.response && error.response.status === 401) {
          try {
            await this.refreshToken();
            const token = await this.getToken();
            error.config.headers.Authorization = `Bearer ${token}`;
            console.log(`🔄 [API] Token yenilendi, istek tekrarlanıyor: ${error.config.method.toUpperCase()} ${error.config.url}`);
            return this.axios.request(error.config);
          } catch (refreshError) {
            await this.logout();
            console.error('🔒 [API] Token yenileme başarısız, çıkış yapılıyor');
            return Promise.reject(refreshError);
          }
        }
        console.error(`❌ [API] Hata yanıtı: ${error.message}`);
        return Promise.reject(error);
      }
    );
  }

  // Token işlemleri
  getToken() {
    const token = localStorage.getItem('access_token');
    return Promise.resolve(token);
  }

  refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return Promise.reject(new Error('Refresh token bulunamadı'));
    }
    
    return axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
      refresh: refreshToken
    }).then(response => {
      localStorage.setItem('access_token', response.data.access);
      return response.data;
    });
  }

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    return Promise.resolve();
  }

  /**
   * API çağrısı esnasında oluşabilecek hataları yönetir
   * @param {Error} error - Hata nesnesi
   * @returns {Object} Hata mesajını içeren obje
   */
  handleError(error) {
    if (error.response) {
      // Sunucu yanıtı ile dönen hata (4xx, 5xx status kodu)
      console.error('🔍 [Hata Detayı] Sunucu yanıtı ile hata:');
      console.error('🔍 [Hata Detayı] Status:', error.response.status);
      console.error('🔍 [Hata Detayı] Status Text:', error.response.statusText);
      console.error('🔍 [Hata Detayı] Headers:', JSON.stringify(error.response.headers, null, 2));
      console.error('🔍 [Hata Detayı] Veri:', JSON.stringify(error.response.data, null, 2));
      
      return {
        success: false,
        status: error.response.status,
        message: error.response.data.message || error.response.data.error || 'Bir hata oluştu',
        data: error.response.data
      };
    } else if (error.request) {
      // İstek yapıldı ama yanıt alınamadı (network hatası, CORS hatası, vs.)
      console.error('🔍 [Hata Detayı] İstek yapıldı ama yanıt alınamadı:');
      console.error('🔍 [Hata Detayı] Error Name:', error.name);
      console.error('🔍 [Hata Detayı] Error Message:', error.message);
      console.error('🔍 [Hata Detayı] URL:', error.config?.url);
      console.error('🔍 [Hata Detayı] Method:', error.config?.method);
      
      return {
        success: false,
        type: 'network_error',
        name: error.name,
        message: 'Sunucudan yanıt alınamadı. Lütfen internet bağlantınızı kontrol edin.'
      };
    } else {
      // İstek yapılmadan önce bir hata oluştu
      console.error('🔍 [Hata Detayı] İstek yapılmadan hata:');
      console.error('🔍 [Hata Detayı] Error Name:', error.name);
      console.error('🔍 [Hata Detayı] Error Message:', error.message);
      console.error('🔍 [Hata Detayı] Stack:', error.stack);
      
      return {
        success: false,
        type: 'request_error',
        name: error.name,
        message: error.message || 'Bir hata oluştu'
      };
    }
  }

  /**
   * Cache işlemleri için yardımcı metodlar
   */
  invalidateCache(cacheKey) {
    if (typeof window !== 'undefined' && window.__SWR__) {
      const cache = window.__SWR__;
      Object.keys(cache).forEach(key => {
        if (key.includes(cacheKey)) {
          cache.delete(key);
        }
      });
    }
  }

  // ========== SWR HOOK'LARI ==========

  /**
   * Tüm gayrimenkulleri getirmek için SWR hook'u
   * @param {Object} params - Query parametreleri
   * @param {Object} options - SWR options
   * @returns {Object} { data, properties, isLoading, isError, mutate }
   */
  useAllProperties = (params = {}, options = {}) => {
    // Query string oluştur
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    const queryString = queryParams.toString();
    
    const { data, error, mutate, isValidating } = useSWR(
      `${API_BASE_URL}/api/properties/?${queryString}`,
      fetcher,
      {
        revalidateOnFocus: false,
        dedupingInterval: 300000, // 5 dakika
        ...options
      }
    );

    return {
      data, 
      properties: data?.results || data || [],
      count: data?.count || 0,
      isLoading: !error && !data,
      isError: !!error,
      mutate,
      isValidating
    };
  }

  /**
   * Belirli bir gayrimenkulün detaylarını getirmek için SWR hook'u
   * @param {number} id - Gayrimenkul ID'si
   * @param {Object} options - SWR options
   * @returns {Object} { property, isLoading, isError, mutate }
   */
  usePropertyDetails = (id, options = {}) => {
    const { data, error, mutate, isValidating } = useSWR(
      id ? `${API_BASE_URL}/api/properties/${id}/` : null,
      fetcher,
      {
        revalidateOnFocus: false,
        dedupingInterval: 300000, // 5 dakika
        ...options
      }
    );

    return {
      property: data || null,
      isLoading: !error && !data && !!id,
      isError: !!error,
      mutate,
      isValidating
    };
  }

  /**
   * Gayrimenkul istatistiklerini getirmek için SWR hook'u
   * @param {Object} options - SWR options
   * @returns {Object} { stats, isLoading, isError, mutate }
   */
  usePropertyStats = (options = {}) => {
    const { data, error, mutate, isValidating } = useSWR(
      `${API_BASE_URL}/api/properties/stats/`,
      fetcher,
      {
        revalidateOnFocus: false,
        dedupingInterval: 600000, // 10 dakika
        ...options
      }
    );

    return {
      stats: data || null,
      isLoading: !error && !data,
      isError: !!error,
      mutate,
      isValidating
    };
  }

  /**
   * Mahalleri getirmek için SWR hook'u
   * @param {Object} params - Query parametreleri
   * @param {Object} options - SWR options
   * @returns {Object} { neighborhoods, isLoading, isError, mutate }
   */
  useNeighborhoods = (params = {}, options = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    const queryString = queryParams.toString();

    const { data, error, mutate, isValidating } = useSWR(
      `${API_BASE_URL}/api/neighborhoods/?${queryString}`,
      fetcher,
      {
        revalidateOnFocus: false,
        dedupingInterval: 600000, // 10 dakika
        ...options
      }
    );

    return {
      neighborhoods: data?.results || data || [],
      isLoading: !error && !data,
      isError: !!error,
      mutate,
      isValidating
    };
  }

  /**
   * FSBO kayıtlarını getirmek için SWR hook'u
   * @param {Object} params - Query parametreleri
   * @param {Object} options - SWR options
   * @returns {Object} { fsboList, isLoading, isError, mutate }
   */
  useFSBOList = (params = {}, options = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    const queryString = queryParams.toString();

    const { data, error, mutate, isValidating } = useSWR(
      `${API_BASE_URL}/api/fsbo/?${queryString}`,
      fetcher,
      {
        revalidateOnFocus: false,
        dedupingInterval: 300000, // 5 dakika
        ...options
      }
    );

    return {
      fsboList: data?.results || data || [],
      count: data?.count || 0,
      isLoading: !error && !data,
      isError: !!error,
      mutate,
      isValidating
    };
  }

  /**
   * Gelişmiş gayrimenkul arama için SWR hook'u
   * @param {Object} searchParams - Arama parametreleri
   * @param {Object} options - SWR options
   * @returns {Object} { searchResults, isLoading, isError, mutate }
   */
  usePropertySearch = (searchParams = {}, options = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(searchParams).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    const queryString = queryParams.toString();

    const shouldFetch = Object.keys(searchParams).length > 0;
    
    const { data, error, mutate, isValidating } = useSWR(
      shouldFetch ? `${API_BASE_URL}/api/properties/search/?${queryString}` : null,
      fetcher,
      {
        revalidateOnFocus: false,
        dedupingInterval: 60000, // 1 dakika
        ...options
      }
    );

    return {
      searchResults: data || null,
      properties: data?.results || [],
      count: data?.count || 0,
      totalPages: data?.total_pages || 0,
      isLoading: !error && !data && shouldFetch,
      isError: !!error,
      mutate,
      isValidating
    };
  }

  /**
   * Öne çıkan gayrimenkulleri getirmek için SWR hook'u
   * @param {Object} options - SWR options
   * @returns {Object} { featuredProperties, isLoading, isError, mutate }
   */
  useFeaturedProperties = (options = {}) => {
    const { data, error, mutate, isValidating } = useSWR(
      `${API_BASE_URL}/api/properties/featured/`,
      fetcher,
      {
        revalidateOnFocus: false,
        dedupingInterval: 600000, // 10 dakika
        ...options
      }
    );

    return {
      featuredProperties: data?.results || data || [],
      count: data?.count || 0,
      isLoading: !error && !data,
      isError: !!error,
      mutate,
      isValidating
    };
  }

  // ========== GAYRİMENKUL İŞLEMLERİ ==========

  /**
   * Tüm gayrimenkulleri getir
   * @param {Object} params - Query parametreleri
   * @returns {Promise} Gayrimenkul listesi
   */
  async getAllProperties(params = {}) {
    try {
      console.log('\n🏠 [API] Tüm gayrimenkuller getiriliyor...');
      
      // Query string oluştur
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, value);
        }
      });
      
      const queryString = queryParams.toString();
      const response = await this.axios.get(`/api/properties/?${queryString}`);
      
      return { success: true, data: response.data };
    } catch (error) {
      console.error('❌ [API] Gayrimenkuller getirme hatası:', error.response?.data || error.message);
      return this.handleError(error);
    }
  }

  /**
   * Gayrimenkul detaylarını getir
   * @param {number} id - Gayrimenkul ID'si
   * @returns {Promise} Gayrimenkul detayları
   */
  async getPropertyDetails(id) {
    try {
      console.log(`\n🏠 [API] "${id}" ID'li gayrimenkul detayları getiriliyor...`);
      
      const response = await this.axios.get(`/api/properties/${id}/`);
      
      return { success: true, data: response.data };
    } catch (error) {
      console.error('❌ [API] Gayrimenkul detayları getirme hatası:', error.response?.data || error.message);
      return this.handleError(error);
    }
  }

  /**
   * Gayrimenkul arama yap
   * @param {Object} searchParams - Arama parametreleri
   * @returns {Promise} Arama sonuçları
   */
  async searchProperties(searchParams = {}) {
    try {
      console.log('\n🔍 [API] Gayrimenkul araması yapılıyor...');
      console.log('🔍 [API] Arama parametreleri:', searchParams);
      
      const queryParams = new URLSearchParams();
      Object.entries(searchParams).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, value);
        }
      });
      
      const queryString = queryParams.toString();
      const response = await this.axios.get(`/api/properties/search/?${queryString}`);
      
      return { success: true, data: response.data };
    } catch (error) {
      console.error('❌ [API] Gayrimenkul arama hatası:', error.response?.data || error.message);
      return this.handleError(error);
    }
  }

  /**
   * Gayrimenkul istatistiklerini getir
   * @returns {Promise} İstatistik verileri
   */
  async getPropertyStats() {
    try {
      console.log('\n📊 [API] Gayrimenkul istatistikleri getiriliyor...');
      
      const response = await this.axios.get('/api/properties/stats/');
      
      return { success: true, data: response.data };
    } catch (error) {
      console.error('❌ [API] Gayrimenkul istatistikleri getirme hatası:', error.response?.data || error.message);
      return this.handleError(error);
    }
  }

  /**
   * Gayrimenkul oluştur (sadece yetkili kullanıcılar için)
   * @param {Object} propertyData - Gayrimenkul verileri
   * @returns {Promise} Oluşturulan gayrimenkul
   */
  async createProperty(propertyData) {
    try {
      console.log('\n🏠 [API] Yeni gayrimenkul oluşturuluyor...');
      
      const response = await this.axios.post('/api/properties/', propertyData);
      
      // Cache'i temizle
      this.invalidateCache(CACHE_KEYS.ALL_PROPERTIES);
      this.invalidateCache(CACHE_KEYS.PROPERTY_STATS);
      
      return { success: true, data: response.data };
    } catch (error) {
      console.error('❌ [API] Gayrimenkul oluşturma hatası:', error.response?.data || error.message);
      return this.handleError(error);
    }
  }

  /**
   * Gayrimenkul güncelle
   * @param {number} id - Gayrimenkul ID'si
   * @param {Object} propertyData - Güncellenecek veriler
   * @returns {Promise} Güncellenen gayrimenkul
   */
  async updateProperty(id, propertyData) {
    try {
      console.log(`\n✏️ [API] "${id}" ID'li gayrimenkul güncelleniyor...`);
      
      const response = await this.axios.patch(`/api/properties/${id}/`, propertyData);
      
      // Cache'i temizle
      this.invalidateCache(CACHE_KEYS.PROPERTY_DETAIL(id));
      this.invalidateCache(CACHE_KEYS.ALL_PROPERTIES);
      
      return { success: true, data: response.data };
    } catch (error) {
      console.error('❌ [API] Gayrimenkul güncelleme hatası:', error.response?.data || error.message);
      return this.handleError(error);
    }
  }

  /**
   * Gayrimenkul sil
   * @param {number} id - Gayrimenkul ID'si
   * @returns {Promise} Silme işlemi sonucu
   */
  async deleteProperty(id) {
    try {
      console.log(`\n🗑️ [API] "${id}" ID'li gayrimenkul siliniyor...`);
      
      const response = await this.axios.delete(`/api/properties/${id}/`);
      
      // Cache'i temizle
      this.invalidateCache(CACHE_KEYS.PROPERTY_DETAIL(id));
      this.invalidateCache(CACHE_KEYS.ALL_PROPERTIES);
      this.invalidateCache(CACHE_KEYS.PROPERTY_STATS);
      
      return { success: true, data: response.data };
    } catch (error) {
      console.error('❌ [API] Gayrimenkul silme hatası:', error.response?.data || error.message);
      return this.handleError(error);
    }
  }

  // ========== MAHALLE İŞLEMLERİ ==========

  /**
   * Tüm mahalleleri getir
   * @param {Object} params - Query parametreleri
   * @returns {Promise} Mahalle listesi
   */
  async getAllNeighborhoods(params = {}) {
    try {
      console.log('\n🏘️ [API] Tüm mahalleler getiriliyor...');
      
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, value);
        }
      });
      
      const queryString = queryParams.toString();
      const response = await this.axios.get(`/api/neighborhoods/?${queryString}`);
      
      return { success: true, data: response.data };
    } catch (error) {
      console.error('❌ [API] Mahalleler getirme hatası:', error.response?.data || error.message);
      return this.handleError(error);
    }
  }

  // ========== FSBO İŞLEMLERİ ==========

  /**
   * FSBO kayıtlarını getir
   * @param {Object} params - Query parametreleri
   * @returns {Promise} FSBO listesi
   */
  async getFSBOList(params = {}) {
    try {
      console.log('\n📞 [API] FSBO kayıtları getiriliyor...');
      
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, value);
        }
      });
      
      const queryString = queryParams.toString();
      const response = await this.axios.get(`/api/fsbo/?${queryString}`);
      
      return { success: true, data: response.data };
    } catch (error) {
      console.error('❌ [API] FSBO kayıtları getirme hatası:', error.response?.data || error.message);
      return this.handleError(error);
    }
  }

  // ========== FİLTRELEME YARDIMCILARı ==========

  /**
   * Fiyat aralığına göre filtrele
   * @param {number} minPrice - Minimum fiyat
   * @param {number} maxPrice - Maksimum fiyat
   * @returns {Object} Filtre parametreleri
   */
  createPriceFilter(minPrice, maxPrice) {
    const filters = {};
    if (minPrice) filters.price__gte = minPrice;
    if (maxPrice) filters.price__lte = maxPrice;
    return filters;
  }

  /**
   * Alan aralığına göre filtrele
   * @param {number} minArea - Minimum alan
   * @param {number} maxArea - Maksimum alan
   * @returns {Object} Filtre parametreleri
   */
  createAreaFilter(minArea, maxArea) {
    const filters = {};
    if (minArea) filters.gross_area__gte = minArea;
    if (maxArea) filters.gross_area__lte = maxArea;
    return filters;
  }

  /**
   * Lokasyon filtreleri oluştur
   * @param {number} cityId - Şehir ID'si
   * @param {number} districtId - İlçe ID'si
   * @param {number} neighborhoodId - Mahalle ID'si
   * @returns {Object} Filtre parametreleri
   */
  createLocationFilter(cityId, districtId, neighborhoodId) {
    const filters = {};
    if (cityId) filters.neighborhood__district__city = cityId;
    if (districtId) filters.neighborhood__district = districtId;
    if (neighborhoodId) filters.neighborhood = neighborhoodId;
    return filters;
  }

  // ========== CACHE İŞLEMLERİ ==========

  /**
   * Tüm gayrimenkul cache'lerini temizle
   */
  clearAllPropertyCaches() {
    console.log('🧹 [Cache] Tüm gayrimenkul önbellekleri temizleniyor...');
    
    this.invalidateCache(CACHE_KEYS.ALL_PROPERTIES);
    this.invalidateCache(CACHE_KEYS.PROPERTY_SEARCH);
    this.invalidateCache(CACHE_KEYS.PROPERTY_STATS);
    this.invalidateCache(CACHE_KEYS.NEIGHBORHOODS);
    this.invalidateCache(CACHE_KEYS.FSBO_LIST);
    
    console.log('✅ [Cache] Tüm gayrimenkul önbellekleri temizlendi');
  }
  
  /**
   * Belirli bir gayrimenkulün cache'ini temizle
   * @param {number} id - Gayrimenkul ID'si
   */
  clearPropertyCache(id) {
    console.log(`🧹 [Cache] "${id}" ID'li gayrimenkul önbelleği temizleniyor...`);
    this.invalidateCache(CACHE_KEYS.PROPERTY_DETAIL(id));
    console.log(`✅ [Cache] "${id}" ID'li gayrimenkul önbelleği temizlendi`);
  }

  /**
   * Öne çıkan gayrimenkulleri getir
   * @param {Object} params - Query parametreleri
   * @returns {Promise} Öne çıkan gayrimenkul listesi
   */
  async getFeaturedProperties(params = {}) {
    try {
      console.log('\n⭐ [API] Öne çıkan gayrimenkuller getiriliyor...');
      
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, value);
        }
      });
      
      const queryString = queryParams.toString();
      const response = await this.axios.get(`/api/properties/featured/?${queryString}`);
      
      return { success: true, data: response.data };
    } catch (error) {
      console.error('❌ [API] Öne çıkan gayrimenkuller getirme hatası:', error.response?.data || error.message);
      return this.handleError(error);
    }
  }
}

// SWR custom hook'ları
export const useAllProperties = (params = {}, options = {}) => {
  const propertyService = new PropertyService();
  return propertyService.useAllProperties(params, options);
};

export const usePropertyDetails = (id, options = {}) => {
  const propertyService = new PropertyService();
  return propertyService.usePropertyDetails(id, options);
};

export const usePropertyStats = (options = {}) => {
  const propertyService = new PropertyService();
  return propertyService.usePropertyStats(options);
};

export const useNeighborhoods = (params = {}, options = {}) => {
  const propertyService = new PropertyService();
  return propertyService.useNeighborhoods(params, options);
};

export const useFSBOList = (params = {}, options = {}) => {
  const propertyService = new PropertyService();
  return propertyService.useFSBOList(params, options);
};

export const usePropertySearch = (searchParams = {}, options = {}) => {
  const propertyService = new PropertyService();
  return propertyService.usePropertySearch(searchParams, options);
};

export const useFeaturedProperties = (options = {}) => {
  const propertyService = new PropertyService();
  return propertyService.useFeaturedProperties(options);
};

// Singleton instance oluştur ve export et
const propertyService = new PropertyService();
export default propertyService; 