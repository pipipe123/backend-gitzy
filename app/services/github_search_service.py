"""
github_search_service.py - Búsqueda de repositorios en GitHub

Este servicio usa la API de búsqueda de GitHub para encontrar repositorios
que coincidan con un texto ingresado por el usuario.

API Endpoint: GET https://api.github.com/search/repositories

Rate Limits:
- Sin autenticación: 10 requests/minuto
- Con token: 30 requests/minuto
"""

# Importa configuración global (tokens)
from app.core.config import settings

# Importa cliente HTTP asíncrono
from app.utils.http_client import get

from app.models.request_models import CATEGORY_TO_TOPICS


def _build_github_query(query: str, filters) -> str:
    """Construye query con qualifiers de GitHub (language:X, topic:Y)."""
    parts = [query]

    if filters is None:
        return query

    if filters.language is not None:
        parts.append(f"language:{filters.language.value}")

    if filters.category is not None:
        topic_keyword = CATEGORY_TO_TOPICS.get(filters.category)
        if topic_keyword:
            parts.append(f"topic:{topic_keyword}")

    if filters.topic is not None:
        parts.append(f"topic:{filters.topic}")

    return "+".join(parts)


async def search_github_repositories(query: str, filters=None):
    """
    Busca repositorios en GitHub usando la Search API.

    Args:
        query: Texto a buscar (ej: "fastapi", "react hooks", "machine learning")

    Returns:
        Lista de diccionarios con información de repositorios encontrados
        Lista vacía si hay error o no hay resultados

    Ejemplo de retorno:
        [
            {
                "provider": "github",
                "name": "fastapi",
                "owner": "tiangolo",
                "description": "FastAPI framework...",
                "url": "https://github.com/tiangolo/fastapi",
                "stars": 50000,
                "language": "Python",
                "updated_at": "2024-01-15T10:30:00Z"
            },
            ...
        ]
    """
    # --- PASO 1: Configurar headers HTTP ---
    # GitHub API requiere el header Accept para especificar la versión de API
    headers = {
        # "application/vnd.github+json" = versión estable de la API v3
        # GitHub puede cambiar la API, este header asegura compatibilidad
        "Accept": "application/vnd.github+json"
    }

    # Si hay token en la configuración, agregarlo al header
    # Beneficios de usar token:
    # - Mayor rate limit (30 req/min vs 10 req/min)
    # - Acceso a repos privados (si el token tiene permisos)
    if settings.GITHUB_TOKEN:
        # "Bearer" es el estándar para tokens OAuth/JWT
        # GitHub requiere este formato específicamente
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    # --- PASO 2: Construir URL de búsqueda ---
    # Parámetros de query:
    # - q={query}: Texto a buscar (se busca en nombre, descripción, README)
    # - sort=stars: Ordena por número de estrellas (más populares primero)
    # - per_page=10: Limita a 10 resultados
    #
    # Otros parámetros disponibles:
    # - sort=forks, sort=updated (otras formas de ordenar)
    # - order=desc, order=asc (orden descendente/ascendente)
    # - page=2 (paginación)
    full_query = _build_github_query(query, filters)
    url = f"https://api.github.com/search/repositories?q={full_query}&sort=stars&per_page=10"

    # --- PASO 3: Hacer petición y procesar respuesta ---
    try:
        # await: Espera la respuesta sin bloquear el servidor
        # Otras peticiones pueden ejecutarse mientras esperamos
        response = await get(url, headers)

        # Verificar código de estado HTTP
        # 200 = OK, 404 = Not Found, 403 = Forbidden (rate limit), etc.
        if response.status_code != 200:
            # Si hay error, retorna lista vacía
            # En producción podríamos loggear el error específico
            return []

        # .json() parsea el string JSON a diccionario Python
        # GitHub devuelve estructura: {"total_count": 123, "items": [...]}
        data = response.json()

        # Inicializa lista para resultados procesados
        results = []

        # --- PASO 4: Procesar cada repositorio ---
        # .get("items", []) obtiene la lista de repos
        # Si no existe "items", usa lista vacía como default
        for repo in data.get("items", []):
            # Extrae y formatea la información relevante
            # .get(key, default) previene errores si un campo no existe
            results.append({
                # "provider": Identifica el origen (github/gitlab/azure)
                "provider": "github",

                # Nombre del repositorio (ej: "fastapi")
                "name": repo.get("name", ""),

                # Dueño del repositorio
                # repo["owner"] es un dict, obtenemos ["owner"]["login"]
                # Si "owner" no existe, usa {}, luego get("login", "")
                "owner": repo.get("owner", {}).get("login", ""),

                # Descripción del repositorio (puede ser None)
                "description": repo.get("description"),

                # URL para acceder al repositorio en el navegador
                "url": repo.get("html_url", ""),

                # Número de estrellas/favoritos
                # .get("stargazers_count", 0) devuelve 0 si no existe
                "stars": repo.get("stargazers_count", 0),

                # Lenguaje principal del repositorio
                # Puede ser None si GitHub no detectó el lenguaje
                "language": repo.get("language"),

                # Fecha de última actualización en formato ISO
                # Ejemplo: "2024-01-15T10:30:00Z"
                "updated_at": repo.get("updated_at", "")
            })

        # Retorna la lista de resultados procesados
        return results

    except Exception as e:
        # Captura CUALQUIER error (red, timeout, JSON inválido, etc.)
        # print() escribe en la consola del servidor
        # En producción usar logging.error() en vez de print()
        print(f"Error buscando en GitHub: {str(e)}")

        # Retorna lista vacía para no romper la aplicación
        # El endpoint combinará resultados de todos los proveedores
        return []
