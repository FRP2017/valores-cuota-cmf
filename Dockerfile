FROM python:3.9-slim

ENV APP_HOME /app
WORKDIR $APP_HOME

# Prevenir que pip guarde en caché para reducir el tamaño de la imagen
ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Copiar el archivo de dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el script de la aplicación
COPY app.py .

# Variable de entorno para el bucket (será sobrescrita por Cloud Run en el despliegue)
ENV GCS_BUCKET_NAME="valores-cuota-cmf"

# Comando para ejecutar la aplicación con Gunicorn
# Cloud Run establece la variable de entorno PORT
CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 300 app:app
