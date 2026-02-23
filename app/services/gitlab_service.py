"""
gitlab_service.py - Búsqueda de repositorios (proyectos) en GitLab

GitLab llama "proyectos" a lo que GitHub llama "repositorios".
Este servicio busca proyectos públicos en GitLab.com

API Endpoint: GET https://gitlab.com/api/v4/projects

Rate Limits:
- Sin autenticación: 300 requests/minuto (mucho más generoso que GitHub)
- Con token: 2000 requests/minuto

Diferencias con GitHub:
- GitLab es más generoso con rate limits
- La API de búsqueda no devuelve el lenguaje principal directamente
- Usa "namespace" en vez de "owner"
"""

import asyncio
from app.core.config import settings
from app.utils.http_client import get
from app.models.request_models import CATEGORY_TO_TOPICS


async def _get_gitlab_project_languages(project_id: int, headers: dict) -> list:
    """Obtiene los lenguajes de un proyecto GitLab."""
    url = f"https://gitlab.com/api/v4/projects/{project_id}/languages"
    try:
        response = await get(url, headers if headers else None)
        if response.status_code == 200:
            # GitLab retorna {"Python": 85.5, "Shell": 14.5}
            return list(response.json().keys())
        return []
    except Exception:
        return []


async def search_gitlab_repositories(query: str, filters=None):
    """
    Busca proyectos en GitLab usando la Projects API.

    Args:
        query: Texto a buscar (busca en nombre y descripción)
        filters: Filtros opcionales (language, category, topic)

    Returns:
        Lista de diccionarios con información de proyectos encontrados
        Lista vacía si hay error o no hay resultados
    """
    # --- PASO 1: Configurar headers ---
    # Inicializamos headers vacío
    headers = {}

    # Si hay token de GitLab en la configuración
    if settings.GITLAB_TOKEN:
        # GitLab usa "PRIVATE-TOKEN" en vez de "Authorization"
        # Diferente a GitHub que usa "Authorization: Bearer TOKEN"
        headers["PRIVATE-TOKEN"] = settings.GITLAB_TOKEN

    # --- PASO 2: Construir URL de búsqueda ---
    need_language_filter = filters is not None and filters.language is not None
    # Si hay filtro de lenguaje, pedimos más resultados para compensar el post-filtrado
    per_page = 30 if need_language_filter else 10

    url = f"https://gitlab.com/api/v4/projects?search={query}&per_page={per_page}&order_by=stars"

    # Agregar filtro de topic (nativo en GitLab)
    if filters is not None:
        if filters.topic is not None:
            url += f"&topic={filters.topic}"
        if filters.category is not None:
            topic_keyword = CATEGORY_TO_TOPICS.get(filters.category)
            if topic_keyword:
                url += f"&topic={topic_keyword}"

    try:
        # --- PASO 3: Hacer petición HTTP ---
        response = await get(url, headers if headers else None)

        # Verificar código de estado
        if response.status_code != 200:
            return []

        # Parsear JSON
        projects = response.json()

        # --- PASO 4: Procesar resultados ---
        if need_language_filter:
            # Obtener lenguajes de todos los proyectos en paralelo
            language_tasks = [
                _get_gitlab_project_languages(project.get("id"), headers)
                for project in projects
            ]
            all_languages = await asyncio.gather(*language_tasks)

            target_language = filters.language.value  # ej: "Python"
            results = []

            for project, languages in zip(projects, all_languages):
                if target_language not in languages:
                    continue

                results.append({
                    "provider": "gitlab",
                    "name": project.get("name", ""),
                    "owner": project.get("namespace", {}).get("name", ""),
                    "description": project.get("description"),
                    "url": project.get("web_url", ""),
                    "stars": project.get("star_count", 0),
                    "language": target_language,
                    "updated_at": project.get("last_activity_at", "")
                })

                if len(results) >= 10:
                    break

            return results
        else:
            # Sin filtro de lenguaje: procesar normalmente
            results = []
            for project in projects:
                results.append({
                    "provider": "gitlab",
                    "name": project.get("name", ""),
                    "owner": project.get("namespace", {}).get("name", ""),
                    "description": project.get("description"),
                    "url": project.get("web_url", ""),
                    "stars": project.get("star_count", 0),
                    "language": None,
                    "updated_at": project.get("last_activity_at", "")
                })
            return results

    except Exception as e:
        print(f"Error buscando en GitLab: {str(e)}")
        return []
