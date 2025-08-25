from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
import json

from .models import Lead, LeadNote, ActionLog
from .survey_models import Survey, SurveyResponse


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def send_satisfaction_survey(request):
    """
    Memnuniyet anketi gönderir
    """
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        
        if not lead_id:
            return JsonResponse({
                'success': False,
                'message': 'Lead ID gerekli'
            })
        
        lead = get_object_or_404(Lead, lead_id=lead_id)
        
        # Mevcut anketi kontrol et
        existing_survey = Survey.objects.filter(
            lead=lead,
            survey_type='satisfaction'
        ).first()
        
        if existing_survey and existing_survey.is_completed:
            return JsonResponse({
                'success': False,
                'message': 'Bu müşteri için zaten tamamlanmış bir anket bulunuyor.'
            })
        
        # Yeni anket oluştur veya mevcut anketi güncelle
        if existing_survey and not existing_survey.is_completed:
            survey = existing_survey
        else:
            survey = Survey.objects.create(
                lead=lead,
                survey_type='satisfaction'
            )
        
        # WhatsApp mesajı gönder
        try:
            from .whatsapp_service import whatsapp_service, WhatsAppTemplates
            
            message_content = WhatsAppTemplates.satisfaction_survey(
                lead.customer_name,
                survey.full_survey_url
            )
            
            result = whatsapp_service.send_text_message(
                lead.customer_phone,
                message_content,
                lead_id=str(lead.lead_id)
            )
            
            if result.get('success'):
                # Anketi gönderildi olarak işaretle
                survey.mark_as_sent(result.get('message_id'))
                
                # Lead note ekle
                LeadNote.objects.create(
                    lead=lead,
                    note_type='whatsapp',
                    title='Memnuniyet Anketi Gönderildi',
                    content=f'WhatsApp üzerinden memnuniyet anketi gönderildi.\nAnket Linki: {survey.full_survey_url}',
                    created_by=request.user
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Memnuniyet anketi başarıyla gönderildi.',
                    'survey_url': survey.full_survey_url
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'WhatsApp mesajı gönderilemedi: {result.get("error", "Bilinmeyen hata")}'
                })
                
        except Exception as wa_error:
            return JsonResponse({
                'success': False,
                'message': f'WhatsApp mesajı gönderilemedi: {str(wa_error)}'
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Hata oluştu: {str(e)}'
        })


@require_http_methods(["GET", "POST"])
def survey_view(request, access_token):
    """
    Anket görüntüleme ve doldurma sayfası
    """
    try:
        survey = get_object_or_404(Survey, access_token=access_token)
        
        # Anketin süresi dolmuş mu kontrol et
        if survey.is_expired:
            return render(request, 'sales_process/survey_expired.html', {
                'survey': survey
            })
        
        # Anket zaten tamamlanmış mı kontrol et
        if survey.is_completed:
            return render(request, 'sales_process/survey_completed.html', {
                'survey': survey
            })
        
        # Görüntülenme sayısını artır
        survey.increment_view_count()
        
        if request.method == 'GET':
            # Anket formunu göster
            return render(request, 'sales_process/survey_form.html', {
                'survey': survey,
                'lead': survey.lead
            })
        
        elif request.method == 'POST':
            # Anket yanıtlarını kaydet
            try:
                # Form verilerini al
                overall_satisfaction = request.POST.get('overall_satisfaction')
                service_quality_rating = request.POST.get('service_quality_rating')
                staff_performance_rating = request.POST.get('staff_performance_rating')
                communication_rating = request.POST.get('communication_rating')
                process_speed_rating = request.POST.get('process_speed_rating')
                
                positive_feedback = request.POST.get('positive_feedback', '').strip()
                improvement_suggestions = request.POST.get('improvement_suggestions', '').strip()
                additional_comments = request.POST.get('additional_comments', '').strip()
                
                would_recommend = request.POST.get('would_recommend')
                referral_likelihood = request.POST.get('referral_likelihood')
                
                # Anket verilerini güncelle
                survey.overall_satisfaction = int(overall_satisfaction) if overall_satisfaction else None
                survey.service_quality_rating = int(service_quality_rating) if service_quality_rating else None
                survey.staff_performance_rating = int(staff_performance_rating) if staff_performance_rating else None
                survey.communication_rating = int(communication_rating) if communication_rating else None
                survey.process_speed_rating = int(process_speed_rating) if process_speed_rating else None
                
                survey.positive_feedback = positive_feedback
                survey.improvement_suggestions = improvement_suggestions
                survey.additional_comments = additional_comments
                
                survey.would_recommend = would_recommend == 'yes' if would_recommend else None
                survey.referral_likelihood = int(referral_likelihood) if referral_likelihood else None
                
                # Anketi tamamlandı olarak işaretle
                survey.mark_as_completed()
                
                # Detaylı yanıtları kaydet
                responses_data = [
                    ('overall_satisfaction', 'Genel Memnuniyet', overall_satisfaction, 'rating'),
                    ('service_quality_rating', 'Hizmet Kalitesi', service_quality_rating, 'rating'),
                    ('staff_performance_rating', 'Personel Performansı', staff_performance_rating, 'rating'),
                    ('communication_rating', 'İletişim', communication_rating, 'rating'),
                    ('process_speed_rating', 'İşlem Hızı', process_speed_rating, 'rating'),
                    ('positive_feedback', 'Olumlu Geri Bildirim', positive_feedback, 'text'),
                    ('improvement_suggestions', 'İyileştirme Önerileri', improvement_suggestions, 'text'),
                    ('additional_comments', 'Ek Yorumlar', additional_comments, 'text'),
                    ('would_recommend', 'Tavsiye Eder misiniz?', would_recommend, 'boolean'),
                    ('referral_likelihood', 'Tavsiye Etme Olasılığı', referral_likelihood, 'rating'),
                ]
                
                for question_key, question_text, answer_value, answer_type in responses_data:
                    if answer_value:
                        SurveyResponse.objects.update_or_create(
                            survey=survey,
                            question_key=question_key,
                            defaults={
                                'question_text': question_text,
                                'answer_value': str(answer_value),
                                'answer_type': answer_type
                            }
                        )
                
                # ActionLog kaydı
                ActionLog.objects.create(
                    lead=survey.lead,
                    action_type='SURVEY_SENT',
                    title='Memnuniyet Anketi Tamamlandı',
                    description=f"Müşteri memnuniyet anketini tamamladı. Genel memnuniyet: {survey.overall_satisfaction}/5",
                    payload={
                        'survey_id': str(survey.survey_id),
                        'overall_satisfaction': survey.overall_satisfaction,
                        'average_rating': survey.average_rating
                    }
                )
                
                # Lead note ekle
                LeadNote.objects.create(
                    lead=survey.lead,
                    note_type='system',
                    title='Memnuniyet Anketi Tamamlandı',
                    content=f'Müşteri memnuniyet anketini tamamladı.\nGenel Memnuniyet: {survey.overall_satisfaction}/5\nOrtalama Puan: {survey.average_rating:.1f}/5' if survey.average_rating else f'Genel Memnuniyet: {survey.overall_satisfaction}/5'
                )
                
                return render(request, 'sales_process/survey_thank_you.html', {
                    'survey': survey,
                    'lead': survey.lead
                })
                
            except Exception as form_error:
                return render(request, 'sales_process/survey_form.html', {
                    'survey': survey,
                    'lead': survey.lead,
                    'error': f'Form işlenirken hata oluştu: {str(form_error)}'
                })
    
    except Survey.DoesNotExist:
        return render(request, 'sales_process/survey_not_found.html')
    except Exception as e:
        return render(request, 'sales_process/survey_error.html', {
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def survey_results(request, survey_id):
    """
    Anket sonuçlarını görüntüler (admin için)
    """
    try:
        survey = get_object_or_404(Survey, survey_id=survey_id)
        responses = SurveyResponse.objects.filter(survey=survey).order_by('created_at')
        
        context = {
            'survey': survey,
            'responses': responses,
            'lead': survey.lead
        }
        
        return render(request, 'sales_process/survey_results.html', context)
        
    except Exception as e:
        messages.error(request, f'Anket sonuçları yüklenirken hata oluştu: {str(e)}')
        return redirect('sales_process:sales_dashboard')


@login_required
@require_http_methods(["POST"])
def send_survey_reminder(request):
    """
    Anket hatırlatması gönderir
    """
    try:
        data = json.loads(request.body)
        survey_id = data.get('survey_id')
        
        if not survey_id:
            return JsonResponse({
                'success': False,
                'message': 'Survey ID gerekli'
            })
        
        survey = get_object_or_404(Survey, survey_id=survey_id)
        
        # Anket tamamlanmış mı kontrol et
        if survey.is_completed:
            return JsonResponse({
                'success': False,
                'message': 'Bu anket zaten tamamlanmış.'
            })
        
        # Anketin süresi dolmuş mu kontrol et
        if survey.is_expired:
            return JsonResponse({
                'success': False,
                'message': 'Bu anketin süresi dolmuş.'
            })
        
        # WhatsApp hatırlatma mesajı gönder
        try:
            from .whatsapp_service import whatsapp_service, WhatsAppTemplates
            
            message_content = WhatsAppTemplates.survey_reminder(
                survey.lead.customer_name,
                survey.full_survey_url
            )
            
            result = whatsapp_service.send_text_message(
                survey.lead.customer_phone,
                message_content,
                lead_id=str(survey.lead.lead_id)
            )
            
            if result.get('success'):
                # Lead note ekle
                LeadNote.objects.create(
                    lead=survey.lead,
                    note_type='whatsapp',
                    title='Anket Hatırlatması Gönderildi',
                    content=f'WhatsApp üzerinden anket hatırlatması gönderildi.\nAnket Linki: {survey.full_survey_url}',
                    created_by=request.user
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Anket hatırlatması başarıyla gönderildi.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'WhatsApp mesajı gönderilemedi: {result.get("error", "Bilinmeyen hata")}'
                })
                
        except Exception as wa_error:
            return JsonResponse({
                'success': False,
                'message': f'WhatsApp mesajı gönderilemedi: {str(wa_error)}'
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Hata oluştu: {str(e)}'
        })