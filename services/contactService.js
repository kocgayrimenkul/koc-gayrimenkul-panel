/**
 * Koç Gayrimenkul - İletişim Service
 * Contact sayfası için API çağrıları
 */

// API base URL - production'da değiştirin
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

class ContactService {
  /**
   * İletişim mesajı gönder
   * @param {Object} formData - Form verileri
   * @param {string} formData.name - Ad soyad
   * @param {string} formData.email - E-posta
   * @param {string} formData.phone - Telefon (opsiyonel)
   * @param {string} formData.property - Gayrimenkul tercihi
   * @param {string} formData.message - Mesaj
   * @returns {Promise<Object>} API yanıtı
   */
  async sendMessage(formData) {
    try {
      // Frontend form field'larını backend field'larına map et
      const payload = {
        name: formData.name?.trim(),
        email: formData.email?.toLowerCase().trim(),
        phone: formData.phone?.trim() || '',
        property_type: this.mapPropertyType(formData.property),
        message: formData.message?.trim()
      };

      // Validasyon
      this.validateFormData(payload);

      const response = await fetch(`${API_BASE_URL}/contact/api/messages/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ContactError(
          errorData.detail || errorData.message || 'Mesaj gönderilemedi',
          response.status,
          errorData
        );
      }

      const result = await response.json();
      
      return {
        success: true,
        message: 'Mesajınız başarıyla gönderildi!',
        data: result
      };

    } catch (error) {
      console.error('Contact service error:', error);
      
      if (error instanceof ContactError) {
        throw error;
      }

      // Network veya diğer hatalar
      throw new ContactError(
        'İletişim servisi ile bağlantı kurulamadı. Lütfen daha sonra tekrar deneyin.',
        0,
        { originalError: error.message }
      );
    }
  }

  /**
   * İletişim mesajları listesini getir (admin için)
   * @param {Object} filters - Filtreleme seçenekleri
   * @returns {Promise<Object>} API yanıtı
   */
  async getMessages(filters = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      if (filters.status) queryParams.append('status', filters.status);
      if (filters.property_type) queryParams.append('property_type', filters.property_type);
      
      const queryString = queryParams.toString();
      const url = `${API_BASE_URL}/contact/api/messages/list/${queryString ? `?${queryString}` : ''}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}` // Admin için auth gerekli
        }
      });

      if (!response.ok) {
        throw new ContactError('Mesajlar yüklenemedi', response.status);
      }

      return await response.json();

    } catch (error) {
      console.error('Get messages error:', error);
      throw error instanceof ContactError ? error : new ContactError('Mesajlar yüklenemedi');
    }
  }

  /**
   * Tek bir mesajı getir
   * @param {number} messageId - Mesaj ID'si
   * @returns {Promise<Object>} API yanıtı
   */
  async getMessage(messageId) {
    try {
      const response = await fetch(`${API_BASE_URL}/contact/api/messages/${messageId}/`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });

      if (!response.ok) {
        throw new ContactError('Mesaj bulunamadı', response.status);
      }

      return await response.json();

    } catch (error) {
      console.error('Get message error:', error);
      throw error instanceof ContactError ? error : new ContactError('Mesaj yüklenemedi');
    }
  }

  /**
   * Mesaj durumunu güncelle
   * @param {number} messageId - Mesaj ID'si
   * @param {Object} updateData - Güncellenecek veriler
   * @returns {Promise<Object>} API yanıtı
   */
  async updateMessage(messageId, updateData) {
    try {
      const response = await fetch(`${API_BASE_URL}/contact/api/messages/${messageId}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        body: JSON.stringify(updateData)
      });

      if (!response.ok) {
        throw new ContactError('Mesaj güncellenemedi', response.status);
      }

      return await response.json();

    } catch (error) {
      console.error('Update message error:', error);
      throw error instanceof ContactError ? error : new ContactError('Mesaj güncellenemedi');
    }
  }

  /**
   * Auth token'ı getir (localStorage'dan veya başka yerden)
   * @returns {string|null} Auth token
   */
  getAuthToken() {
    // Bu kısım auth yapınıza göre değişecek
    return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
  }

  /**
   * Frontend property values'ları backend'e uygun hale getir
   * @param {string} frontendValue - Frontend'den gelen değer
   * @returns {string} Backend için uygun değer
   */
  mapPropertyType(frontendValue) {
    const mappings = {
      'Satılık': 'satilik',
      'Kiralık': 'kiralik', 
      'Proje': 'proje',
      'Diğer': 'diger',
      'satilik': 'satilik',
      'kiralik': 'kiralik',
      'proje': 'proje',
      'diger': 'diger',
      '': ''
    };

    return mappings[frontendValue] || 'diger';
  }

  /**
   * Form verilerini validate et
   * @param {Object} payload - Gönderilecek veri
   * @throws {ContactError} Validasyon hatası
   */
  validateFormData(payload) {
    const errors = [];

    // Ad soyad kontrolü
    if (!payload.name || payload.name.length < 2) {
      errors.push('Ad soyad en az 2 karakter olmalıdır');
    }

    // E-posta kontrolü
    if (!payload.email) {
      errors.push('E-posta adresi gereklidir');
    } else if (!this.isValidEmail(payload.email)) {
      errors.push('Geçerli bir e-posta adresi giriniz');
    }

    // Mesaj kontrolü
    if (!payload.message || payload.message.length < 10) {
      errors.push('Mesaj en az 10 karakter olmalıdır');
    }

    // Telefon kontrolü (opsiyonel ama girildiyse geçerli olmalı)
    if (payload.phone && !this.isValidPhone(payload.phone)) {
      errors.push('Geçerli bir telefon numarası giriniz');
    }

    if (errors.length > 0) {
      throw new ContactError(
        'Form bilgilerinde hatalar var',
        400,
        { validationErrors: errors }
      );
    }
  }

  /**
   * E-posta format kontrolü
   * @param {string} email - E-posta adresi
   * @returns {boolean} Geçerli mi?
   */
  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Telefon format kontrolü
   * @param {string} phone - Telefon numarası
   * @returns {boolean} Geçerli mi?
   */
  isValidPhone(phone) {
    // Türk telefon numarası formatları için basit kontrol
    const cleaned = phone.replace(/[\s\-\(\)]/g, '');
    const phoneRegex = /^(\+90|0)?[5][0-9]{9}$/;
    return phoneRegex.test(cleaned);
  }

  /**
   * Rate limiting kontrol et
   * @returns {boolean} Mesaj gönderilebilir mi?
   */
  checkRateLimit() {
    const lastSent = localStorage.getItem('lastContactMessage');
    if (!lastSent) return true;

    const timeDiff = Date.now() - parseInt(lastSent);
    const minInterval = 60000; // 1 dakika

    return timeDiff > minInterval;
  }

  /**
   * Rate limit kaydet
   */
  setRateLimit() {
    localStorage.setItem('lastContactMessage', Date.now().toString());
  }

  /**
   * Form'u resetle sonrasında cache temizle
   */
  clearFormCache() {
    localStorage.removeItem('contactFormData');
  }

  /**
   * Form verilerini geçici olarak kaydet
   * @param {Object} formData - Form verileri
   */
  saveFormToCache(formData) {
    try {
      localStorage.setItem('contactFormData', JSON.stringify(formData));
    } catch (error) {
      console.warn('Form cache kaydedilemedi:', error);
    }
  }

  /**
   * Cache'den form verilerini getir
   * @returns {Object|null} Kaydedilmiş form verileri
   */
  getFormFromCache() {
    try {
      const cached = localStorage.getItem('contactFormData');
      return cached ? JSON.parse(cached) : null;
    } catch (error) {
      console.warn('Form cache okunamadı:', error);
      return null;
    }
  }
}

/**
 * Custom Contact Error Class
 */
class ContactError extends Error {
  constructor(message, status = 0, details = {}) {
    super(message);
    this.name = 'ContactError';
    this.status = status;
    this.details = details;
  }

  /**
   * Kullanıcı dostu hata mesajı
   * @returns {string} Gösterilecek mesaj
   */
  getUserMessage() {
    switch (this.status) {
      case 400:
        return this.details.validationErrors 
          ? this.details.validationErrors.join(', ')
          : 'Form bilgilerini kontrol ediniz';
      case 429:
        return 'Çok fazla mesaj gönderdiniz. Lütfen bir süre bekleyiniz';
      case 500:
        return 'Sunucu hatası oluştu. Lütfen daha sonra tekrar deneyin';
      default:
        return this.message || 'Beklenmeyen bir hata oluştu';
    }
  }

  /**
   * Hata türü kontrolü
   * @returns {boolean} Validasyon hatası mı?
   */
  isValidationError() {
    return this.status === 400 && this.details.validationErrors;
  }

  /**
   * Hata türü kontrolü
   * @returns {boolean} Rate limit hatası mı?
   */
  isRateLimitError() {
    return this.status === 429;
  }

  /**
   * Hata türü kontrolü
   * @returns {boolean} Server hatası mı?
   */
  isServerError() {
    return this.status >= 500;
  }
}

// Singleton instance
const contactService = new ContactService();

export { ContactService, ContactError };
export default contactService; 