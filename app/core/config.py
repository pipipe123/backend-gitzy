"""
config.py - Configuración global y variables de entorno

Este archivo centraliza todas las configuraciones de la aplicación:
- Tokens de API (GitHub, GitLab, Azure)
- Configuración de cookies (nombre, duración, secret key)
- Variables de entorno desde el archivo .env

Todos los demás módulos importan 'settings' desde aquí.
"""

# Módulo 'os' para interactuar con el sistema operativo
# Principalmente usado para leer variables de entorno
import os

# python-dotenv carga variables desde el archivo .env
# Hace que las variables definidas en .env estén disponibles con os.getenv()
from dotenv import load_dotenv

# Ejecuta la carga del archivo .env
# Busca un archivo .env en el directorio actual y carga sus variables
# Ejemplo: GITHUB_TOKEN=abc123 en .env → os.getenv("GITHUB_TOKEN") = "abc123"
load_dotenv()

# Clase Settings contiene toda la configuración de la aplicación
# Se crea como clase para organizar las configuraciones y facilitar el acceso
class Settings:
    # Token de autenticación de GitHub
    # Se obtiene desde la variable de entorno GITHUB_TOKEN
    # Necesario para hacer peticiones a la API de GitHub sin límites estrictos
    # Sin token: 60 requests/hora, Con token: 5000 requests/hora
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN")

    # Token de autenticación de GitLab (opcional)
    # Si no está definido en .env, se usa string vacío ""
    # GitLab permite búsquedas públicas sin token, pero con límites menores
    GITLAB_TOKEN: str = os.getenv("GITLAB_TOKEN", "")

    # Token de autenticación de Azure DevOps (opcional)
    # Azure DevOps requiere token para cualquier operación
    # Sin token, las búsquedas en Azure retornarán vacías
    AZURE_TOKEN: str = os.getenv("AZURE_TOKEN", "")

    # --- Configuración de Cookies ---

    # SECRET_KEY: Clave secreta para firmar cookies (seguridad)
    # En producción DEBE cambiarse por un valor aleatorio y seguro
    # Ejemplo de generación: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu-secreto-super-seguro-cambialo-en-produccion")

    # COOKIE_NAME: Nombre de la cookie que se enviará al navegador
    # El navegador guardará una cookie con este nombre
    # Valor: UUID único por usuario (ej: "a3f2c1b4-...")
    COOKIE_NAME: str = "session_id"

    # COOKIE_MAX_AGE: Tiempo de vida de la cookie en segundos
    # Cálculo: 30 días * 24 horas * 60 minutos * 60 segundos = 2,592,000 segundos
    # Después de 30 días, el navegador eliminará automáticamente la cookie
    COOKIE_MAX_AGE: int = 30 * 24 * 60 * 60

# Crea una instancia única (singleton) de la clase Settings
# Todos los demás archivos importarán esta instancia: from app.core.config import settings
# Esto asegura que toda la app use la misma configuración
settings = Settings()
