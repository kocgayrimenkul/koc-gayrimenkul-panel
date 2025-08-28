# -*- encoding: utf-8 -*-
"""
Koç Gayrimenkul Panel - Satış Süreç Yönetimi Test Dosyası
"""

from django.test import TestCase, Client
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    Lead, SalesStage, Task, LeadNote, StageTransition, 
    Appointment, WhatsAppMessage, CallLog, LeadAssignment
)
from .assignment_service import AssignmentService
from apps.customers.models import Customer, Neighborhood

User = get_user_model()


class SalesProcessModelTests(TestCase):
    """Test cases for sales process models"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Manager'
        )
        
        self.agent = User.objects.create_user(
            username='agent',
            email='agent@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Agent'
        )
        
        # Create groups
        self.managers_group = Group.objects.create(name='Managers')
        self.sales_staff_group = Group.objects.create(name='Sales_Staff')
        
        self.manager.groups.add(self.managers_group)
        self.agent.groups.add(self.sales_staff_group)
        
        # Create neighborhood
        self.neighborhood = Neighborhood.objects.create(
            name='Test Mahalle',
            district='Test İlçe'
        )
        
        # Create customer
        self.customer = Customer.objects.create(
            full_name='Test Customer',
            phone='+905551234567',
            neighborhood=self.neighborhood,
            consultant=self.agent
        )
        
        # Create sales stages
        self.stage_new = SalesStage.objects.create(
            name='Yeni Lead',
            slug='new',
            stage_type='staff',
            order=1,
            is_active=True
        )
        
        self.stage_contacted = SalesStage.objects.create(
            name='İletişim Kuruldu',
            slug='contacted',
            stage_type='staff',
            order=2,
            is_active=True
        )
        
        self.stage_closed_won = SalesStage.objects.create(
            name='Satış Tamamlandı',
            slug='closed-won',
            stage_type='manager',
            order=6,
            is_active=True
        )
    
    def test_lead_creation(self):
        """Test lead creation"""
        lead = Lead.objects.create(
            customer=self.customer,
            customer_name='John Doe',
            customer_phone='+905551234567',
            source='referans',
            priority=3,
            current_stage=self.stage_new,
            assigned_staff=self.agent
        )
        
        self.assertEqual(lead.customer_name, 'John Doe')
        self.assertEqual(lead.customer_phone, '+905551234567')
        self.assertEqual(lead.current_stage, self.stage_new)
        self.assertEqual(lead.assigned_staff, self.agent)
        self.assertEqual(lead.status, 'active')
    
    def test_stage_transition(self):
        """Test stage transition functionality"""
        lead = Lead.objects.create(
            customer=self.customer,
            customer_name='Jane Smith',
            customer_phone='+905559876543',
            source='referans',
            priority=4,
            current_stage=self.stage_new,
            assigned_staff=self.agent
        )
        
        # Create stage transition
        transition = StageTransition.objects.create(
            lead=lead,
            from_stage=self.stage_new,
            to_stage=self.stage_contacted,
            transition_type='manual',
            performed_by=self.agent,
            reason='İlk görüşme yapıldı'
        )
        
        # Update lead stage
        lead.current_stage = self.stage_contacted
        lead.save()
        
        self.assertEqual(transition.lead, lead)
        self.assertEqual(transition.from_stage, self.stage_new)
        self.assertEqual(transition.to_stage, self.stage_contacted)
        self.assertEqual(transition.performed_by, self.agent)
        self.assertEqual(lead.current_stage, self.stage_contacted)


class AssignmentServiceTests(TestCase):
    """Test cases for assignment service"""
    
    def setUp(self):
        """Set up test data"""
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123'
        )
        
        self.agent1 = User.objects.create_user(
            username='agent1',
            email='agent1@test.com',
            password='testpass123',
            is_staff=True
        )
        
        self.agent2 = User.objects.create_user(
            username='agent2',
            email='agent2@test.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create groups
        sales_group = Group.objects.create(name='Sales_Staff')
        self.agent1.groups.add(sales_group)
        self.agent2.groups.add(sales_group)
        
        # Create neighborhood
        self.neighborhood = Neighborhood.objects.create(
            name='Test Mahalle',
            district='Test İlçe'
        )
        
        # Create customer
        self.customer = Customer.objects.create(
            full_name='Test Customer',
            phone='+905551234567',
            neighborhood=self.neighborhood,
            consultant=self.agent1
        )
        
        # Create stages
        self.stage = SalesStage.objects.create(
            name='Yeni Lead',
            slug='new',
            stage_type='staff',
            order=1,
            is_active=True
        )
        
        # Create all required stages for views
        SalesStage.objects.create(
            name='bilgi_verildi',
            slug='bilgi-verildi',
            stage_type='staff',
            order=2,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='ihtiyac_analizi',
            slug='ihtiyac-analizi',
            stage_type='staff',
            order=3,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='teklif_gonderildi',
            slug='teklif-gonderildi',
            stage_type='staff',
            order=4,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='daire_sunumu',
            slug='daire-sunumu',
            stage_type='staff',
            order=5,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='cevap_bekleniyor',
            slug='cevap-bekleniyor',
            stage_type='staff',
            order=6,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='sozlesme_yapildi',
            slug='sozlesme-yapildi',
            stage_type='manager',
            order=7,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='kredi_islemleri',
            slug='kredi-islemleri',
            stage_type='manager',
            order=8,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='tapu_islemi',
            slug='tapu-islemi',
            stage_type='manager',
            order=9,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='hizmet_tamamlandi',
            slug='hizmet-tamamlandi',
            stage_type='manager',
            order=10,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='memnuniyet_anketi',
            slug='memnuniyet-anketi',
            stage_type='manager',
            order=11,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='dosya_kapandi',
            slug='dosya-kapandi',
            stage_type='manager',
            order=12,
            is_active=True
        )
        
        self.assignment_service = AssignmentService()
    
    def test_auto_assign_lead(self):
        """Test automatic lead assignment"""
        lead = Lead.objects.create(
            customer=self.customer,
            customer_name='Test Lead',
            customer_phone='+905551234567',
            source='referans',
            priority=3,
            current_stage=self.stage
        )
        
        result = self.assignment_service.auto_assign_lead(lead)
        
        self.assertTrue(result)
        lead.refresh_from_db()
        self.assertIsNotNone(lead.assigned_staff)
        self.assertIn(lead.assigned_staff, [self.agent1, self.agent2])


class SalesProcessViewTests(TestCase):
    """Test cases for sales process views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123'
        )
        self.manager.is_staff = True
        self.manager.save()
        
        self.agent = User.objects.create_user(
            username='agent',
            email='agent@test.com',
            password='testpass123'
        )
        
        # Create groups
        managers_group = Group.objects.create(name='Managers')
        sales_group = Group.objects.create(name='Sales_Staff')
        
        self.manager.groups.add(managers_group)
        self.agent.groups.add(sales_group)
        
        # Create neighborhood
        self.neighborhood = Neighborhood.objects.create(
            name='Test Mahalle',
            district='Test İlçe'
        )
        
        # Create customer
        self.customer = Customer.objects.create(
            full_name='Test Customer',
            phone='+905551234567',
            neighborhood=self.neighborhood,
            consultant=self.agent
        )
        
        # Create stages
        self.stage = SalesStage.objects.create(
            name='Yeni Lead',
            slug='new',
            stage_type='staff',
            order=1,
            is_active=True
        )
        
        # Create all required stages for views
        SalesStage.objects.create(
            name='bilgi_verildi',
            slug='bilgi-verildi',
            stage_type='staff',
            order=2,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='ihtiyac_analizi',
            slug='ihtiyac-analizi',
            stage_type='staff',
            order=3,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='teklif_gonderildi',
            slug='teklif-gonderildi',
            stage_type='staff',
            order=4,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='daire_sunumu',
            slug='daire-sunumu',
            stage_type='staff',
            order=5,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='cevap_bekleniyor',
            slug='cevap-bekleniyor',
            stage_type='staff',
            order=6,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='sozlesme_yapildi',
            slug='sozlesme-yapildi',
            stage_type='manager',
            order=7,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='kredi_islemleri',
            slug='kredi-islemleri',
            stage_type='manager',
            order=8,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='tapu_islemi',
            slug='tapu-islemi',
            stage_type='manager',
            order=9,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='hizmet_tamamlandi',
            slug='hizmet-tamamlandi',
            stage_type='manager',
            order=10,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='memnuniyet_anketi',
            slug='memnuniyet-anketi',
            stage_type='manager',
            order=11,
            is_active=True
        )
        
        SalesStage.objects.create(
            name='dosya_kapandi',
            slug='dosya-kapandi',
            stage_type='manager',
            order=12,
            is_active=True
        )
    
    def test_sales_dashboard_access(self):
        """Test sales dashboard access"""
        # Test unauthenticated access
        response = self.client.get(reverse('sales_process:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test authenticated access
        self.client.login(username='agent', password='testpass123')
        response = self.client.get(reverse('sales_process:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_staff_kanban_access(self):
        """Test staff kanban access"""
        self.client.login(username='agent', password='testpass123')
        response = self.client.get(reverse('sales_process:staff_kanban'))
        self.assertEqual(response.status_code, 200)
    
    def test_manager_kanban_access(self):
        """Test manager kanban access"""
        # Test manager access
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('sales_process:manager_kanban'))
        self.assertEqual(response.status_code, 200)
    
    def test_lead_creation_view(self):
        """Test lead creation via view"""
        self.client.login(username='agent', password='testpass123')
        
        # Test GET request first
        response = self.client.get(reverse('sales_process:lead_create'))
        self.assertEqual(response.status_code, 200)
        
        # Test POST request
        lead_data = {
            'customer_name': 'Test User',
            'customer_phone': '+905551234567',
            'property_type': 'apartment',
            'property_location': 'Test Location',
            'budget_min': '100000',
            'budget_max': '200000'
        }
        
        response = self.client.post(reverse('sales_process:lead_create'), lead_data)
        # Should return JSON response
        self.assertIn(response.status_code, [200, 302])
    
    def test_ajax_leads_retrieval(self):
        """Test AJAX leads retrieval"""
        self.client.login(username='agent', password='testpass123')
        
        # Create test lead
        lead = Lead.objects.create(
            customer=self.customer,
            customer_name='AJAX Test',
            customer_phone='+905559999999',
            source='referans',
            priority=4,
            current_stage=self.stage,
            assigned_staff=self.agent
        )
        
        response = self.client.get(
            reverse('sales_process:get_leads_ajax'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('leads', data)
        self.assertIn('statistics', data)


class WhatsAppIntegrationTests(TestCase):
    """Test cases for WhatsApp integration"""
    
    def setUp(self):
        """Set up test data"""
        self.agent = User.objects.create_user(
            username='agent',
            email='agent@test.com',
            password='testpass123'
        )
        
        # Create neighborhood
        self.neighborhood = Neighborhood.objects.create(
            name='Test Mahalle',
            district='Test İlçe'
        )
        
        # Create customer
        self.customer = Customer.objects.create(
            full_name='WhatsApp Test Customer',
            phone='+905551234567',
            neighborhood=self.neighborhood,
            consultant=self.agent
        )
        
        self.stage = SalesStage.objects.create(
            name='Yeni Lead',
            slug='new',
            stage_type='staff',
            order=1,
            is_active=True
        )
        
        self.lead = Lead.objects.create(
            customer=self.customer,
            customer_name='WhatsApp Test',
            customer_phone='+905551234567',
            source='whatsapp',
            priority=3,
            current_stage=self.stage,
            assigned_staff=self.agent
        )
    
    def test_whatsapp_message_creation(self):
        """Test WhatsApp message creation"""
        message = WhatsAppMessage.objects.create(
            lead=self.lead,
            message_id='wamid.test123',
            message_type='text',
            content='Test message',
            direction='inbound',
            status='delivered'
        )
        
        self.assertEqual(message.lead, self.lead)
        self.assertEqual(message.message_id, 'wamid.test123')
        self.assertEqual(message.content, 'Test message')
        self.assertEqual(message.direction, 'inbound')
        self.assertEqual(message.status, 'delivered')


class CallLogTests(TestCase):
    """Test cases for call logging"""
    
    def setUp(self):
        """Set up test data"""
        self.agent = User.objects.create_user(
            username='agent',
            email='agent@test.com',
            password='testpass123'
        )
        
        # Create neighborhood
        self.neighborhood = Neighborhood.objects.create(
            name='Test Mahalle',
            district='Test İlçe'
        )
        
        # Create customer
        self.customer = Customer.objects.create(
            full_name='Call Test Customer',
            phone='+905551234567',
            neighborhood=self.neighborhood,
            consultant=self.agent
        )
        
        self.stage = SalesStage.objects.create(
            name='Yeni Lead',
            slug='new',
            stage_type='staff',
            order=1,
            is_active=True
        )
        
        self.lead = Lead.objects.create(
            customer=self.customer,
            customer_name='Call Test',
            customer_phone='+905551234567',
            source='referans',
            priority=4,
            current_stage=self.stage,
            assigned_staff=self.agent
        )
    
    def test_call_log_creation(self):
        """Test call log creation"""
        call_log = CallLog.objects.create(
            lead=self.lead,
            call_id='call_test_123',
            caller_number='+905551234567',
            called_number='+905559876543',
            call_type='outbound',
            duration_seconds=120,
            status='answered',
            started_at=timezone.now(),
            recording_url='https://example.com/recording.mp3',
            notes='Successful call'
        )
        
        self.assertEqual(call_log.lead, self.lead)
        self.assertEqual(call_log.caller_number, '+905551234567')
        self.assertEqual(call_log.call_type, 'outbound')
        self.assertEqual(call_log.duration_seconds, 120)
        self.assertEqual(call_log.status, 'answered')


class TaskManagementTests(TestCase):
    """Test cases for task management"""
    
    def setUp(self):
        """Set up test data"""
        self.agent = User.objects.create_user(
            username='agent',
            email='agent@test.com',
            password='testpass123'
        )
        
        # Create neighborhood
        self.neighborhood = Neighborhood.objects.create(
            name='Test Mahalle',
            district='Test İlçe'
        )
        
        # Create customer
        self.customer = Customer.objects.create(
            full_name='Task Test Customer',
            phone='+905551234567',
            neighborhood=self.neighborhood,
            consultant=self.agent
        )
        
        self.stage = SalesStage.objects.create(
            name='Yeni Lead',
            slug='new',
            stage_type='staff',
            order=1,
            is_active=True
        )
        
        self.lead = Lead.objects.create(
            customer=self.customer,
            customer_name='Task Test',
            customer_phone='+905551234567',
            source='referans',
            priority=3,
            current_stage=self.stage,
            assigned_staff=self.agent
        )
    
    def test_task_creation(self):
        """Test task creation"""
        task = Task.objects.create(
            lead=self.lead,
            title='Follow up call',
            description='Call the lead to discuss property options',
            task_type='call',
            priority=4,
            assigned_to=self.agent,
            due_date=timezone.now() + timedelta(days=1),
            status='pending'
        )
        
        self.assertEqual(task.lead, self.lead)
        self.assertEqual(task.title, 'Follow up call')
        self.assertEqual(task.task_type, 'call')
        self.assertEqual(task.priority, 4)
        self.assertEqual(task.assigned_to, self.agent)
        self.assertEqual(task.status, 'pending')
    
    def test_task_completion(self):
        """Test task completion"""
        task = Task.objects.create(
            lead=self.lead,
            title='Send brochure',
            description='Send property brochure via email',
            task_type='email',
            priority=3,
            assigned_to=self.agent,
            due_date=timezone.now() + timedelta(hours=2),
            status='pending'
        )
        
        # Complete the task
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        self.assertEqual(task.status, 'completed')
        self.assertIsNotNone(task.completed_at)


class ReportingTests(TestCase):
    """Test cases for reporting functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123'
        )
        
        self.agent1 = User.objects.create_user(
            username='agent1',
            email='agent1@test.com',
            password='testpass123'
        )
        
        self.agent2 = User.objects.create_user(
            username='agent2',
            email='agent2@test.com',
            password='testpass123'
        )
        
        # Create neighborhood
        self.neighborhood = Neighborhood.objects.create(
            name='Test Mahalle',
            district='Test İlçe'
        )
        
        # Create customers
        self.customer1 = Customer.objects.create(
            full_name='Report Test Customer 1',
            phone='+905551111111',
            neighborhood=self.neighborhood,
            consultant=self.agent1
        )
        
        self.customer2 = Customer.objects.create(
            full_name='Report Test Customer 2',
            phone='+905552222222',
            neighborhood=self.neighborhood,
            consultant=self.agent2
        )
        
        # Create stages
        self.stage_new = SalesStage.objects.create(
            name='Yeni Lead',
            slug='new',
            stage_type='staff',
            order=1,
            is_active=True
        )
        
        self.stage_won = SalesStage.objects.create(
            name='Satış Tamamlandı',
            slug='closed-won',
            stage_type='manager',
            order=6,
            is_active=True
        )
        
        # Create test leads
        self.lead1 = Lead.objects.create(
            customer=self.customer1,
            customer_name='Report Test1',
            customer_phone='+905551111111',
            source='referans',
            priority=4,
            current_stage=self.stage_won,
            assigned_staff=self.agent1
        )
        
        self.lead2 = Lead.objects.create(
            customer=self.customer2,
            customer_name='Report Test2',
            customer_phone='+905552222222',
            source='branda',
            priority=3,
            current_stage=self.stage_new,
            assigned_staff=self.agent2
        )
    
    def test_conversion_rate_calculation(self):
        """Test conversion rate calculation"""
        # Agent1 has 1 lead, 1 won (100% conversion)
        # Agent2 has 1 lead, 0 won (0% conversion)
        
        agent1_leads = Lead.objects.filter(assigned_staff=self.agent1)
        agent1_won = agent1_leads.filter(current_stage__slug='closed-won')
        agent1_conversion = (agent1_won.count() / agent1_leads.count()) * 100 if agent1_leads.count() > 0 else 0
        
        agent2_leads = Lead.objects.filter(assigned_staff=self.agent2)
        agent2_won = agent2_leads.filter(current_stage__slug='closed-won')
        agent2_conversion = (agent2_won.count() / agent2_leads.count()) * 100 if agent2_leads.count() > 0 else 0
        
        self.assertEqual(agent1_conversion, 100.0)
        self.assertEqual(agent2_conversion, 0.0)
    
    def test_agent_performance_metrics(self):
        """Test agent performance metrics"""
        # Test lead count per agent
        agent1_lead_count = Lead.objects.filter(assigned_staff=self.agent1).count()
        agent2_lead_count = Lead.objects.filter(assigned_staff=self.agent2).count()
        
        self.assertEqual(agent1_lead_count, 1)
        self.assertEqual(agent2_lead_count, 1)
        
        # Test active leads
        agent1_active = Lead.objects.filter(assigned_staff=self.agent1, status='active').count()
        agent2_active = Lead.objects.filter(assigned_staff=self.agent2, status='active').count()
        
        self.assertEqual(agent1_active, 1)
        self.assertEqual(agent2_active, 1)
