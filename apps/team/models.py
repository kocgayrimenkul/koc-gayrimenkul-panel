from django.db import models
from django.utils import timezone
from django.core.validators import URLValidator


class TeamMember(models.Model):
    """
    Web sitesinde gösterilecek ekip üyelerini yönetir
    """
    POSITION_CHOICES = [
        ('ceo', 'CEO & Kurucu'),
        ('manager', 'Müdür'),
        ('consultant', 'Gayrimenkul Danışmanı'),
        ('senior_consultant', 'Kıdemli Gayrimenkul Danışmanı'),
        ('specialist', 'Uzman'),
        ('coordinator', 'Koordinatör'),
        ('assistant', 'Asistan'),
        ('other', 'Diğer'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name="Ad Soyad",
        help_text="Ekip üyesinin tam adı"
    )
    
    position = models.CharField(
        max_length=50,
        choices=POSITION_CHOICES,
        verbose_name="Pozisyon",
        help_text="Ekip üyesinin pozisyonu"
    )
    
    custom_position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Özel Pozisyon",
        help_text="Listede olmayan özel pozisyon girebilirsiniz"
    )
    
    image = models.ImageField(
        upload_to='team/',
        blank=True,
        null=True,
        verbose_name="Fotoğraf",
        help_text="Ekip üyesinin fotoğrafı (önerilen boyut: 250x250px)"
    )
    
    image_url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator()],
        verbose_name="Fotoğraf URL",
        help_text="Harici bir fotoğraf URL'si (fotoğraf yüklenmemişse kullanılır)"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif",
        help_text="Web sitesinde gösterilsin mi?"
    )
    
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Sıralama",
        help_text="Web sitesinde gösterilme sırası (küçük sayı önce gösterilir)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Oluşturulma Tarihi"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Güncellenme Tarihi"
    )

    class Meta:
        verbose_name = "Ekip Üyesi"
        verbose_name_plural = "Ekip Üyeleri"
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} - {self.get_position_display()}"

    def get_position_display_custom(self):
        """Özel pozisyon varsa onu, yoksa seçili pozisyonu döndürür"""
        if self.custom_position:
            return self.custom_position
        return self.get_position_display()

    def get_image_url(self):
        """Fotoğraf URL'sini döndürür (yüklenen dosya veya harici URL)"""
        if self.image:
            return self.image.url
        elif self.image_url:
            return self.image_url
        return None
