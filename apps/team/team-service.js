// services/team-service.js
// Koç Gayrimenkul - Ekip Üyeleri Service

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Ekip üyeleri API service'i
 */
class TeamService {
  
  /**
   * Aktif ekip üyelerinin listesini getir
   * @returns {Promise<Object>} Ekip üyeleri listesi
   */
  async getTeamList() {
    try {
      const response = await fetch(`${API_BASE_URL}/team/api/list/`, {
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
        data: data.team_members || []
      };
    } catch (error) {
      console.error('Ekip üyeleri alınırken hata:', error);
      return {
        success: false,
        error: error.message,
        data: []
      };
    }
  }

  /**
   * Ekip üyesi için placeholder avatar URL'si oluştur
   * @param {Object} member - Ekip üyesi verisi
   * @returns {string} Placeholder avatar URL'si
   */
  getAvatarPlaceholder(member) {
    if (!member || !member.name) {
      return `https://ui-avatars.com/api/?name=?&background=9d2235&color=fff&size=200`;
    }

    const initials = member.name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);

    return `https://ui-avatars.com/api/?name=${encodeURIComponent(initials)}&background=9d2235&color=fff&size=200`;
  }
}

// Singleton instance
const teamService = new TeamService();

export default teamService; 