import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from apps.employees.models import EmployeeProfile
from apps.customers.models import Neighborhood

consultants = EmployeeProfile.objects.filter(role='consultant', is_active=True).select_related('user')

print('--- DANISMANLAR ---')
for c in consultants:
    username = c.user.username
    fullname = c.user.get_full_name() or '(bos)'
    email = c.user.email or '(email yok)'
    print(f'  Kullanici: {username}  |  Isim: {fullname}  |  Email: {email}')
print(f'Toplam: {consultants.count()} danisman')
print('')
print('--- MAHALLELER ---')
for n in Neighborhood.objects.all().order_by('name'):
    owner = n.consultant.username if n.consultant else '(atanmamis)'
    print(f'  {n.name}  ->  {owner}')