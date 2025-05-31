## Ejecución Local (para pruebas)

1.  Clona el repositorio.
2.  Crea y activa un entorno virtual:
    ```cmd
    python -m venv .venv
    .venv\Scripts\activate
    ```
    *(Si usas PowerShell, el comando de activación es `.venv\Scripts\Activate.ps1`)*
3.  Instala las dependencias:
    ```cmd
    pip install -r requirements.txt
    ```
4.  Establece la variable de entorno `GCS_BUCKET_NAME` (solo para la sesión actual del CMD):
    ```cmd
    set GCS_BUCKET_NAME=valores-cuota-cmf
    ```
    *(Si quieres que persista para futuras sesiones de CMD, usa `setx GCS_BUCKET_NAME "valores-cuota-cmf"` y luego reinicia tu CMD. Para PowerShell, sería `$env:GCS_BUCKET_NAME="valores-cuota-cmf"` para la sesión actual)*
5.  Ejecuta la aplicación Flask localmente:
    ```cmd
    python app.py
    ```
    La aplicación estará disponible en `http://localhost:8080` (o el puerto que se muestre). Puedes hacer una solicitud GET o POST a esta URL para probar la descarga y subida.


    holahola