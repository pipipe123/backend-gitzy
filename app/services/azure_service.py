"""
azure_service.py - Búsqueda de repositorios en Azure DevOps

Busca repositorios Git dentro de una organización de Azure DevOps.
Requiere AZURE_TOKEN (PAT) y AZURE_ORGANIZATION en variables de entorno.

API Endpoint: GET https://dev.azure.com/{org}/_apis/git/repositories?api-version=7.0

Autenticación: Basic auth con PAT (Personal Access Token)
- Header: Authorization: Basic base64(:{token})

Rate Limits: 200 requests/minuto con token
"""

import base64

from app.core.config import settings
from app.utils.http_client import get
from app.models.request_models import CATEGORY_TO_TOPICS


def _get_azure_headers() -> dict:
    """Construye headers de autenticación para Azure DevOps."""
    credentials = base64.b64encode(f":{settings.AZURE_TOKEN}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }


async def search_azure_repositories(query: str, filters=None):
    """
    Busca repositorios en Azure DevOps listando repos de la organización
    y filtrando por nombre/descripción.

    Azure DevOps no tiene una API de búsqueda global como GitHub/GitLab,
    así que lista todos los repos de la organización y filtra localmente.
    """
    if not settings.AZURE_TOKEN or not settings.AZURE_ORGANIZATION:
        return []

    headers = _get_azure_headers()
    org = settings.AZURE_ORGANIZATION

    url = f"https://dev.azure.com/{org}/_apis/git/repositories?api-version=7.0"

    try:
        response = await get(url, headers)

        if response.status_code != 200:
            return []

        data = response.json()
        repos = data.get("value", [])

        # Filtrar localmente por query (nombre o descripción)
        query_lower = query.lower()
        matched = [
            repo for repo in repos
            if query_lower in repo.get("name", "").lower()
        ]

        # Limitar a 10 resultados
        matched = matched[:10]

        results = []
        for repo in matched:
            project = repo.get("project", {})
            results.append({
                "provider": "azure",
                "name": repo.get("name", ""),
                "owner": project.get("name", org),
                "description": project.get("description"),
                "url": repo.get("webUrl", ""),
                "stars": 0,  # Azure DevOps no tiene concepto de estrellas
                "language": None,  # Azure no expone lenguaje en la API de repos
                "updated_at": project.get("lastUpdateTime", "")
            })

        return results

    except Exception as e:
        print(f"Error buscando en Azure DevOps: {str(e)}")
        return []
