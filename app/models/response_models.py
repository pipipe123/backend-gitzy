"""
response_models.py - Modelos de salida (Response Models)

Define la estructura de las respuestas JSON que devuelve la API.
FastAPI usa estos modelos para:
1. Validar que las respuestas tengan la estructura correcta
2. Generar documentación automática (Swagger/OpenAPI)
3. Serializar objetos Python a JSON

Si un endpoint intenta devolver datos que no coinciden con su modelo,
FastAPI lanzará un error en tiempo de desarrollo.
"""

# BaseModel: Clase base de Pydantic para modelos con validación
from pydantic import BaseModel

# List: Indica una lista de elementos del mismo tipo
# Optional: Indica que un campo puede ser None (null en JSON)
# Any: Indica que el tipo puede ser cualquier cosa
from typing import List, Optional, Any


# Modelo para representar un commit de Git
# Usado dentro de RepositoryResponse
class Commit(BaseModel):
    sha: str           # Hash único del commit (ej: "a3f2c1b4...")
    message: str       # Mensaje del commit (ej: "Fix bug in login")
    author: Optional[str]  # Nombre del autor (puede ser None si no está disponible)


# Modelo para la respuesta del endpoint POST /repository/analyze
# Devuelve información COMPLETA de un repositorio específico
class RepositoryResponse(BaseModel):
    provider: str              # Proveedor: "github", "gitlab" o "azure"
    name: str                  # Nombre del repositorio (ej: "fastapi")
    owner: str                 # Usuario u organización dueña (ej: "tiangolo")
    description: Optional[str] # Descripción del repo (puede ser None si no tiene)
    is_private: bool           # True si es repositorio privado, False si es público
    default_branch: str        # Rama principal (ej: "main", "master", "develop")
    created_at: str            # Fecha de creación en formato ISO (ej: "2018-12-05T13:05:32Z")
    updated_at: str            # Fecha de última actualización en formato ISO
    stars: int                 # Número de estrellas/favoritos
    forks: int                 # Número de forks (copias del repositorio)
    open_issues: int           # Número de issues abiertos
    languages: List[str]       # Lista de lenguajes usados (ej: ["Python", "JavaScript"])
    commits: List[Commit]      # Lista de últimos commits (objetos Commit)
    url: str                   # URL completa al repositorio


# Modelo para un resultado individual de búsqueda
# Usado dentro de SearchResponse como lista de resultados
class SearchResultItem(BaseModel):
    provider: str              # Proveedor donde se encontró: "github", "gitlab", "azure"
    name: str                  # Nombre del repositorio
    owner: str                 # Dueño del repositorio
    description: Optional[str] # Descripción (puede ser None)
    url: str                   # URL para acceder al repositorio
    stars: int                 # Número de estrellas/favoritos
    language: Optional[str]    # Lenguaje principal (puede ser None si no está disponible)
    updated_at: str            # Fecha de última actualización en formato ISO


# Modelo para la respuesta del endpoint POST /repository/search
# Devuelve resultados de búsqueda en GitHub, GitLab y Azure DevOps
class SearchResponse(BaseModel):
    query: str                      # Texto que se buscó (ej: "fastapi")
    filters: Optional[dict] = None  # Filtros aplicados (language, category, topic)
    results: List[SearchResultItem] # Lista de repositorios encontrados
    total_results: int              # Número total de resultados (len(results))


# Modelo para la respuesta del endpoint GET /repository/session
# Devuelve información de la sesión del usuario guardada en la cookie
class SessionResponse(BaseModel):
    session_id: str                 # UUID de la sesión (ej: "a3f2c1b4-...")
    last_search_query: Optional[str]# Última búsqueda realizada (None si no ha buscado nada)
    last_search_filters: Optional[dict] = None  # Últimos filtros aplicados
    last_results: List[Any]         # Últimos resultados guardados (tipo genérico)
    searches_count: int             # Número total de búsquedas realizadas por el usuario