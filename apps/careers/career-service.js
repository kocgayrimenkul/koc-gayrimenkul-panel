// services/career-service.js
// Koç Gayrimenkul - İş Başvurusu Service

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * İş başvurusu API service'i
 */
class CareerService {
  
  /**
   * Pozisyon ve deneyim seçeneklerini getir
   * @returns {Promise<Object>} Pozisyon ve deneyim seçenekleri
   */
  async getApplicationChoices() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/careers/applications/choices/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data: data
      };
    } catch (error) {
      console.error('Seçenekler alınırken hata:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * İş başvurusu gönder
   * @param {Object} applicationData - Başvuru verileri
   * @param {File} cvFile - CV dosyası
   * @returns {Promise<Object>} API yanıtı
   */
  async submitApplication(applicationData, cvFile) {
    try {
      // FormData oluştur (CV dosyası için)
      const formData = new FormData();
      
      // Başvuru verilerini ekle
      Object.keys(applicationData).forEach(key => {
        if (applicationData[key] !== null && applicationData[key] !== undefined) {
          formData.append(key, applicationData[key]);
        }
      });

      // CV dosyasını ekle
      if (cvFile) {
        formData.append('cv_file', cvFile);
      }

      const response = await fetch(`${API_BASE_URL}/api/careers/applications/`, {
        method: 'POST',
        body: formData, // Content-Type header'ını otomatik ayarlar
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data,
          status: response.status
        };
      }

      return {
        success: true,
        data: data
      };
    } catch (error) {
      console.error('Başvuru gönderilirken hata:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Başvuru verilerini doğrula (frontend validation)
   * @param {Object} data - Başvuru verileri
   * @param {File} cvFile - CV dosyası
   * @returns {Object} Doğrulama sonucu
   */
  validateApplication(data, cvFile) {
    const errors = {};

    // Zorunlu alanları kontrol et
    if (!data.first_name?.trim()) {
      errors.first_name = 'Ad alanı zorunludur';
    }

    if (!data.last_name?.trim()) {
      errors.last_name = 'Soyad alanı zorunludur';
    }

    if (!data.email?.trim()) {
      errors.email = 'E-posta alanı zorunludur';
    } else if (!this.validateEmail(data.email)) {
      errors.email = 'Geçerli bir e-posta adresi giriniz';
    }

    if (!data.phone?.trim()) {
      errors.phone = 'Telefon alanı zorunludur';
    } else if (!this.validatePhone(data.phone)) {
      errors.phone = 'Geçerli bir telefon numarası giriniz';
    }

    if (!data.position) {
      errors.position = 'Pozisyon seçimi zorunludur';
    }

    if (!data.experience) {
      errors.experience = 'Deneyim süresi seçimi zorunludur';
    }

    if (!data.cover_letter?.trim()) {
      errors.cover_letter = 'Ön yazı/açıklama alanı zorunludur';
    } else if (data.cover_letter.length < 50) {
      errors.cover_letter = 'Ön yazı en az 50 karakter olmalıdır';
    }

    // CV dosyası kontrolü
    if (!cvFile) {
      errors.cv_file = 'CV dosyası zorunludur';
    } else {
      const cvValidation = this.validateCVFile(cvFile);
      if (!cvValidation.valid) {
        errors.cv_file = cvValidation.error;
      }
    }

    return {
      valid: Object.keys(errors).length === 0,
      errors
    };
  }

  /**
   * E-posta formatını doğrula
   * @param {string} email 
   * @returns {boolean}
   */
  validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Telefon formatını doğrula
   * @param {string} phone 
   * @returns {boolean}
   */
  validatePhone(phone) {
    // Türkiye telefon numarası formatları
    const phoneRegex = /^(\+90|0)?[0-9]{10}$/;
    const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
    return phoneRegex.test(cleanPhone);
  }

  /**
   * CV dosyasını doğrula
   * @param {File} file 
   * @returns {Object}
   */
  validateCVFile(file) {
    const maxSize = 5 * 1024 * 1024; // 5MB
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const allowedExtensions = ['.pdf', '.doc', '.docx'];

    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'CV dosyası 5MB\'dan büyük olamaz'
      };
    }

    const fileName = file.name.toLowerCase();
    const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
    
    if (!hasValidExtension || !allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'CV dosyası PDF, DOC veya DOCX formatında olmalıdır'
      };
    }

    return {
      valid: true
    };
  }

  /**
   * Telefon numarasını temizle ve formatla
   * @param {string} phone 
   * @returns {string}
   */
  formatPhone(phone) {
    const cleaned = phone.replace(/[\s\-\(\)]/g, '');
    
    // 0 ile başlıyorsa kaldır
    if (cleaned.startsWith('0')) {
      return cleaned.substring(1);
    }
    
    // +90 ile başlıyorsa kaldır
    if (cleaned.startsWith('+90')) {
      return cleaned.substring(3);
    }
    
    // 90 ile başlıyorsa kaldır (13 haneli durumda)
    if (cleaned.length === 12 && cleaned.startsWith('90')) {
      return cleaned.substring(2);
    }
    
    return cleaned;
  }

  /**
   * Başvuru sonucu için kullanıcı dostu mesaj
   * @param {Object} result - API sonucu
   * @returns {string}
   */
  getResultMessage(result) {
    if (result.success) {
      return 'İş başvurunuz başarıyla alındı. En kısa sürede sizinle iletişime geçeceğiz.';
    }

    if (result.error) {
      // Backend'den gelen hata mesajları
      if (typeof result.error === 'object') {
        const errorMessages = [];
        
        Object.keys(result.error).forEach(field => {
          const errors = Array.isArray(result.error[field]) 
            ? result.error[field] 
            : [result.error[field]];
          
          errors.forEach(error => {
            errorMessages.push(error);
          });
        });
        
        return errorMessages.join('\n');
      }
      
      return result.error;
    }

    return 'Bir hata oluştu. Lütfen tekrar deneyin.';
  }
}

// Singleton instance
const careerService = new CareerService();

export default careerService; 