# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Satış Süreç İzin Sistemi Test Dosyası
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from apps.employees.models import EmployeeProfile
from apps.customers.models import Customer, Neighborhood
from .decorators import (
    require_role_level, require_lead_access, require_manager_or_admin_level,
    get_user_role_level, can_access_user_data, ROLE_HIERARCHY
)
from .models import Lead, SalesStage

User = get_user_model()


class PermissionSystemTestCase(TestCase):
    """Permission sistemi test sınıfı"""
    
    def setUp(self):
        """Test verilerini hazırla"""
        self.factory = RequestFactory()
        
        # Test kullanıcıları oluştur
        self.admin_user = User.objects.create_user(
            username='admin', email='admin@test.com', password='test123'
        )
        self.manager_user = User.objects.create_user(
            username='manager', email='manager@test.com', password='test123'
        )
        self.consultant_user = User.objects.create_user(
            username='consultant', email='consultant@test.com', password='test123'
        )
        self.secretary_user = User.objects.create_user(
            username='secretary', email='secretary@test.com', password='test123'
        )
        
        # Employee profilleri oluştur
        EmployeeProfile.objects.create(
            user=self.admin_user, role='admin', is_active=True
        )
        EmployeeProfile.objects.create(
            user=self.manager_user, role='manager', is_active=True
        )
        EmployeeProfile.objects.create(
            user=self.consultant_user, role='consultant', is_active=True
        )
        EmployeeProfile.objects.create(
            user=self.secretary_user, role='secretary', is_active=True
        )
        
        # Test customer ve lead'i oluştur
        neighborhood = Neighborhood.objects.create(name='Test Mahalle')
        customer = Customer.objects.create(
            full_name='Test Customer',
            phone='1234567890',
            neighborhood=neighborhood
        )
        stage = SalesStage.objects.create(name='test_stage', order=1)
        self.test_lead = Lead.objects.create(
            customer=customer,
            customer_name='Test Customer',
            customer_phone='1234567890',
            source='referans',
            assigned_staff=self.consultant_user,
            current_stage=stage
        )
        
        # Başka consultant için lead
        self.other_lead = Lead.objects.create(
            customer=customer,
            customer_name='Test Customer 2',
            customer_phone='0987654321',
            source='referans',
            current_stage=stage
        )
    
    def test_role_hierarchy(self):
        """Rol hiyerarşisini test et"""
        self.assertEqual(get_user_role_level(self.admin_user), 100)
        self.assertEqual(get_user_role_level(self.manager_user), 80)
        self.assertEqual(get_user_role_level(self.consultant_user), 60)
        self.assertEqual(get_user_role_level(self.secretary_user), 40)
    
    def test_user_data_access(self):
        """Kullanıcı veri erişim kontrolünü test et"""
        # Admin herkese erişebilir
        self.assertTrue(can_access_user_data(self.admin_user, self.consultant_user))
        
        # Manager consultant'a erişebilir
        self.assertTrue(can_access_user_data(self.manager_user, self.consultant_user))
        
        # Consultant manager'a erişemez
        self.assertFalse(can_access_user_data(self.consultant_user, self.manager_user))
        
        # Consultant kendine erişebilir
        self.assertTrue(can_access_user_data(self.consultant_user, self.consultant_user))
    
    def test_lead_ownership_access(self):
        """Lead sahiplik erişim kontrolünü test et"""
        # Lead sahibi erişebilir (AJAX request)
        request = self.factory.get('/test/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.consultant_user
        self._add_session_and_messages(request)
        
        @require_lead_access('view')
        def test_view(request, lead_id):
            return JsonResponse({'success': True})
        
        response = test_view(request, lead_id=self.test_lead.id)
        self.assertEqual(response.status_code, 200)
        
        # Başka consultant erişemez (AJAX request)
        other_consultant = User.objects.create_user(
            username='other_consultant', email='other@test.com', password='test123'
        )
        EmployeeProfile.objects.create(
            user=other_consultant, role='consultant', is_active=True
        )
        
        # Other consultant kendi lead'ine sahip olsun
        self.other_lead.assigned_staff = other_consultant
        self.other_lead.save()
        
        # Other consultant başka birinin lead'ine erişmeye çalışsın
        request = self.factory.get('/test/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = other_consultant
        self._add_session_and_messages(request)
        response = test_view(request, lead_id=self.test_lead.id)  # consultant_user'ın lead'i
        self.assertEqual(response.status_code, 403)
        
        # Manager erişebilir (AJAX request)
        request = self.factory.get('/test/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.manager_user
        self._add_session_and_messages(request)
        response = test_view(request, lead_id=self.test_lead.id)
        self.assertEqual(response.status_code, 200)
    
    def test_manager_level_access(self):
        """Manager seviye erişim kontrolünü test et"""
        @require_manager_or_admin_level
        def test_view(request):
            return JsonResponse({'success': True})
        
        # Consultant erişemez (AJAX request)
        request = self.factory.get('/test/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.consultant_user
        self._add_session_and_messages(request)
        response = test_view(request)
        self.assertEqual(response.status_code, 403)
        
        # Manager erişebilir (AJAX request)
        request = self.factory.get('/test/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.manager_user
        self._add_session_and_messages(request)
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Admin erişebilir (AJAX request)
        request = self.factory.get('/test/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.admin_user
        self._add_session_and_messages(request)
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
    
    def _add_session_and_messages(self, request):
        """Request'e session ve messages ekle"""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)


if __name__ == '__main__':
    # Test'leri çalıştırmak için:
    # python manage.py test apps.sales_process.test_permissions
    pass