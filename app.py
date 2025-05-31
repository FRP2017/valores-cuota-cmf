import os
import requests
from datetime import datetime, timedelta, date
from urllib.parse import urlencode
from google.cloud import storage
from flask import Flask, request
import re

app = Flask(__name__)

# Configuración
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")
DOWNLOAD_DIR = "/tmp/downloads" # Carpeta para descargas temporales en el contenedor

def download_file_and_upload_to_gcs():
    print(f"Iniciando descarga directa del archivo. Directorio temporal: {DOWNLOAD_DIR}")
    # Para ejecución local en Windows, considera la modificación de DOWNLOAD_DIR que te sugerí antes si esto falla después.
    # Por ahora, nos enfocamos en el error 403.
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    base_url = "https://www.cmfchile.cl/institucional/estadisticas/fm.fm_bpr_dia.php"
    
    fecha_actual_servidor = date.today()
    target_date = fecha_actual_servidor - timedelta(days=5)
    dia_descarga = str(target_date.day)
    mes_descarga = target_date.strftime("%m")
    anio_descarga = str(target_date.year)

    print(f"Fecha actual del servidor: {fecha_actual_servidor.strftime('%Y-%m-%d')}")
    print(f"Fecha calculada para la descarga (actual - 5 días): {dia_descarga}/{mes_descarga}/{anio_descarga}")
    
    params = {
        "admins": "0",
        "tipofondo": "0",
        "moneda": "0",
        "dia_select": dia_descarga,
        "mes_peri": mes_descarga,
        "anio_peri": anio_descarga,
        "out": "excel",
        "lang": "es"
    }

    query_string = urlencode(params)
    full_url = f"{base_url}?{query_string}"

    print(f"Solicitando URL: {full_url}")

    downloaded_file_path = None
    original_filename = f"datos_cmf_{anio_descarga}{mes_descarga.zfill(2)}{dia_descarga.zfill(2)}.xls" 

    try:
        # --- AÑADIR CABECERA USER-AGENT ---
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(full_url, headers=headers, stream=True, timeout=180)
        # --- FIN DE LA MODIFICACIÓN ---
        
        response.raise_for_status() # Esto lanzará una excepción si el código es 4xx o 5xx

        content_disposition = response.headers.get('content-disposition')
        if content_disposition:
            match = re.search(r'filename="?([^"]+)"?', content_disposition)
            if match:
                original_filename = match.group(1)
                print(f"Nombre de archivo detectado de Content-Disposition: {original_filename}")
            else:
                print(f"No se pudo extraer nombre de Content-Disposition: {content_disposition}. Usando: {original_filename}")
        else:
            print(f"Cabecera Content-Disposition no encontrada. Usando: {original_filename}")
        
        sanitized_original_filename = "".join(c if c.isalnum() or c in ('.', '_', '-') else '_' for c in original_filename)
        if not sanitized_original_filename.lower().endswith(('.xls', '.xlsx')):
            sanitized_original_filename += ".xls"

        downloaded_file_path = os.path.join(DOWNLOAD_DIR, sanitized_original_filename)

        with open(downloaded_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Archivo descargado exitosamente en: {downloaded_file_path}")

        if not GCS_BUCKET_NAME:
            print("Error CRÍTICO: GCS_BUCKET_NAME no está configurado en las variables de entorno. No se puede subir el archivo.")
            return "Error: GCS_BUCKET_NAME no configurado.", 500
            
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        blob_folder = f"cmf-valores-cuota/{target_date.strftime('%Y/%m/%d')}"
        date_str_upload_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        blob_name = f"{blob_folder}/{date_str_upload_timestamp}-{sanitized_original_filename}"
        
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(downloaded_file_path)
        print(f"Archivo {downloaded_file_path} subido a gs://{GCS_BUCKET_NAME}/{blob_name}")

        return f"Proceso completado. Archivo para fecha {target_date.strftime('%Y-%m-%d')} subido a gs://{GCS_BUCKET_NAME}/{blob_name}", 200

    except requests.exceptions.HTTPError as http_err:
        print(f"Error HTTP durante la solicitud: {http_err}") # Esto fue lo que viste
        print(f"Contenido de la respuesta (si existe): {http_err.response.text[:500] if hasattr(http_err.response, 'text') else 'No response content or content type not text'}")
        return f"Error HTTP durante la solicitud: {str(http_err)}", getattr(http_err.response, 'status_code', 500)
    except requests.exceptions.RequestException as e:
        print(f"Error durante la solicitud HTTP: {e}")
        return f"Error durante la solicitud HTTP: {str(e)}", 500
    except Exception as e:
        print(f"Ocurrió un error general: {e}")
        return f"Error durante el proceso: {str(e)}", 500
    finally:
        if downloaded_file_path and os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)
            print(f"Archivo local {downloaded_file_path} eliminado.")

@app.route("/", methods=["GET", "POST"])
def handle_request():
    try:
        print(f"Solicitud recibida. Headers: {request.headers}")
        message, status_code = download_file_and_upload_to_gcs()
        return message, status_code
    except Exception as e:
        print(f"Error crítico en handle_request: {e}")
        return f"Error interno del servidor en handle_request: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    
    current_gcs_bucket_name = os.environ.get("GCS_BUCKET_NAME")
    
    if not current_gcs_bucket_name and not os.environ.get("K_SERVICE"):
        print("--------------------------------------------------------------------")
        print("ADVERTENCIA: GCS_BUCKET_NAME no está configurado para ejecución local.")
        print("Para pruebas locales, establece la variable de entorno antes de ejecutar el script:")
        print("En Windows CMD: set GCS_BUCKET_NAME=valores-cuota-cmf")
        print("En PowerShell:  $env:GCS_BUCKET_NAME='valores-cuota-cmf'")
        print("--------------------------------------------------------------------")
    
    print(f"Iniciando Flask app en http://0.0.0.0:{port} para pruebas locales...")
    app.run(host="0.0.0.0", port=port, debug=True)