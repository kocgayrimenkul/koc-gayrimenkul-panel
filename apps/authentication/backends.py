from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Kullanıcı adı veya e-posta adresi ile kimlik doğrulama sağlayan backend.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Kullanıcı adı veya e-posta ile kullanıcıyı sorgulama
            user = User.objects.get(Q(username=username) | Q(email=username))
            
            # Şifre kontrolü
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # Kullanıcı bulunamadı
            return None
        
        return None 