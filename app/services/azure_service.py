from app.core.config import settings
from app.utils.http_client import get


async def search_azure_repositories(query: str, filters=None):
    """Busca repositorios en Azure DevOps"""
    if not settings.AZURE_TOKEN:
        return []

    # Azure DevOps requiere organización específica
    # Este es un ejemplo básico, necesitarías configurar tu org
    headers = {
        "Authorization": f"Basic {settings.AZURE_TOKEN}",
        "Content-Type": "application/json"
    }

    # Nota: Azure DevOps API requiere especificar una organización
    # Por ahora retorna vacío si no está configurado correctamente
    try:
        # Aquí iría la lógica específica de Azure DevOps
        # que requiere configuración de organización
        return []
    except Exception as e:
        print(f"Error buscando en Azure DevOps: {str(e)}")
        return []
