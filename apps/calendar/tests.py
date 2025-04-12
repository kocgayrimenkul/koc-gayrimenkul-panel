# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Takvim/Ajanda Testleri
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Event, TodoItem
from datetime import timedelta

# Buraya test sınıfları eklenebilir
# class EventModelTest(TestCase):
#     def setUp(self):
#         # Test için gerekli verileri oluştur
#         self.user = User.objects.create_user(username='testuser', password='12345')
#         
#     def test_event_creation(self):
#         # Event oluşturma testi
#         event = Event.objects.create(
#             title="Test Event",
#             event_type="meeting",
#             start_time=timezone.now(),
#             end_time=timezone.now() + timedelta(hours=1),
#             consultant=self.user
#         )
#         self.assertEqual(event.title, "Test Event")
#         self.assertFalse(event.is_completed) 