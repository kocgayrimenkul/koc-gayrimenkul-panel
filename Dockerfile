# Resmi Python 3.10 görüntüsünü kullanın
FROM python:3.10

# Python'un pyc dosyalarını diske yazmasını engeller (python -B seçeneği ile eşdeğer)
ENV PYTHONDONTWRITEBYTECODE 1

# Python'un stdout ve stderr'yi tamponlamasını engeller (python -u seçeneği ile eşdeğer)
ENV PYTHONUNBUFFERED 1

# Konteyner içinde çalışma dizinini /app olarak ayarlayın
WORKDIR /app

# Mevcut dizin içeriğini konteynerin /app dizinine kopyalayın
COPY . .

# Gereksinimleri yükleyin
RUN pip install --no-cache-dir -r requirements.txt

# Statik dosyaları topla
RUN python manage.py collectstatic --noinput

# Portları açın
EXPOSE 8000

# Uygulamayı Gunicorn ile belirtilen portta çalıştırın
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]