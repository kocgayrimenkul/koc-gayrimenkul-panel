from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Cep Telefonu')
    extension = models.CharField(max_length=10, blank=True, null=True, verbose_name='Dahili Numara')
    
    class Meta:
        verbose_name = 'Kullanıcı Profili'
        verbose_name_plural = 'Kullanıcı Profilleri'
    
    def __str__(self):
        return f"{self.user.username} - {self.phone}"