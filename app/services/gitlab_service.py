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

from app.core.config import settings
from app.utils.http_client import get


async def search_gitlab_repositories(query: str):
    """
    Busca proyectos en GitLab usando la Projects API.

    Args:
        query: Texto a buscar (busca en nombre y descripción)

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
    # Parámetros:
    # - search={query}: Texto a buscar (en nombre y descripción)
    # - per_page=10: Limita a 10 resultados
    # - order_by=stars: Ordena por número de estrellas (star_count)
    #
    # Otros parámetros disponibles:
    # - order_by=last_activity_at (más recientes)
    # - order_by=created_at (más nuevos)
    # - visibility=public (solo públicos, es el default)
    url = f"https://gitlab.com/api/v4/projects?search={query}&per_page=10&order_by=stars"

    try:
        # --- PASO 3: Hacer petición HTTP ---
        # Si headers está vacío (no hay token), pasa None
        # "headers if headers else None" = pasa headers solo si tiene contenido
        response = await get(url, headers if headers else None)

        # Verificar código de estado
        if response.status_code != 200:
            # Error: retorna lista vacía
            return []

        # Parsear JSON
        # GitLab devuelve directamente una lista de proyectos
        # (diferente a GitHub que devuelve {"items": [...]})
        projects = response.json()

        # Inicializar lista de resultados
        results = []

        # --- PASO 4: Procesar cada proyecto ---
        for project in projects:
            results.append({
                # Identificador del proveedor
                "provider": "gitlab",

                # Nombre del proyecto
                "name": project.get("name", ""),

                # Dueño del proyecto
                # En GitLab se llama "namespace" (usuario o grupo)
                # project["namespace"] es un dict con {"name": "...", "path": "..."}
                "owner": project.get("namespace", {}).get("name", ""),

                # Descripción del proyecto
                "description": project.get("description"),

                # URL web del proyecto
                "url": project.get("web_url", ""),

                # Número de estrellas
                "stars": project.get("star_count", 0),

                # ⚠️ LIMITACIÓN: GitLab API de búsqueda no incluye lenguaje principal
                # Para obtener el lenguaje, necesitaríamos hacer una petición
                # adicional por cada proyecto: GET /projects/:id/languages
                # Esto sería muy lento (10 proyectos = 10 peticiones extra)
                # Por eso dejamos language como None
                "language": None,

                # Fecha de última actividad (commits, merge requests, etc.)
                # "last_activity_at" es más preciso que "updated_at"
                "updated_at": project.get("last_activity_at", "")
            })

        # Retornar resultados procesados
        return results

    except Exception as e:
        # Capturar cualquier error
        print(f"Error buscando en GitLab: {str(e)}")
        return []
