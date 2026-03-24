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
    summary: Optional["RepositorySummary"] = None  # Resumen general del análisis


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
class TreeNode(BaseModel):
    name: str
    path: str
    type: str
    size: Optional[int] = None
    children: Optional[List["TreeNode"]] = None


TreeNode.model_rebuild()


class RepositoryStructureResponse(BaseModel):
    provider: str
    owner: str
    name: str
    default_branch: str
    total_files: int
    total_directories: int
    tree: List[TreeNode]


class FileContentResponse(BaseModel):
    provider: str              # "github", "gitlab" o "azure"
    repo_name: str             # Nombre del repositorio
    file_path: str             # Ruta completa del archivo en el repo
    file_name: str             # Nombre del archivo (ej: "main.py")
    content: str               # Contenido del archivo (texto o base64 si es binario)
    encoding: str              # "utf-8" o "base64"
    size: Optional[int] = None # Tamaño en bytes
    is_binary: bool = False    # True si el archivo es binario


class FunctionMetrics(BaseModel):
    name: str
    line_start: int
    line_end: int
    lines: int
    cyclomatic_complexity: int


class FileMetrics(BaseModel):
    path: str
    functions: List[FunctionMetrics]
    comment_lines: int
    code_lines: int
    blank_lines: int
    comment_code_ratio: float


class MetricsSummary(BaseModel):
    avg_cyclomatic_complexity: float
    avg_lines_per_function: float
    comment_code_ratio: float
    total_functions: int
    total_lines_of_code: int
    total_comment_lines: int


class MetricsResponse(BaseModel):
    provider: str
    owner: str
    name: str
    language: str
    files_analyzed: int
    files_skipped: int
    summary: MetricsSummary
    files: List[FileMetrics]


class RepositorySummary(BaseModel):
    popularity_level: str          # "Muy popular", "Popular", "Moderado", "Bajo", "Nuevo"
    activity_level: str            # "Muy activo", "Activo", "Moderado", "Bajo", "Inactivo"
    languages_count: int           # Cantidad de lenguajes detectados
    primary_language: Optional[str]  # Lenguaje principal (primero de la lista)
    health_score: float            # Puntuación de salud 0-100
    description: str               # Resumen en texto natural del repositorio


class AISummaryResponse(BaseModel):
    provider: str
    owner: str
    name: str
    ai_summary: str


class CodeAnalysisResponse(BaseModel):
    file_path: str
    language: str
    quality_score: int
    summary: str
    strengths: List[str]
    improvements: List[str]
    patterns: List[str]


class CodeSuggestion(BaseModel):
    file_name: str
    title: str
    description: str
    severity: str              # "high", "medium", "low"
    line_start: int
    line_end: int
    original_snippet: str
    suggested_snippet: str


class FileSuggestionsResult(BaseModel):
    file_name: str
    language: str
    suggestions: List[CodeSuggestion]
    improved_code: str
    diff: str


class CodeSuggestionsResponse(BaseModel):
    total_suggestions: int
    files: List[FileSuggestionsResult]


class HistoryEntry(BaseModel):
    entry_id: str
    action: str                    # "analyze", "ai_summary", "ai_code_analysis", "ai_suggestions"
    provider: Optional[str] = None
    repo_name: Optional[str] = None
    repo_owner: Optional[str] = None
    url: Optional[str] = None
    details: dict = {}
    timestamp: str


class HistoryResponse(BaseModel):
    session_id: str
    total_entries: int
    entries: List[HistoryEntry]


class SessionResponse(BaseModel):
    session_id: str                 # UUID de la sesión (ej: "a3f2c1b4-...")
    last_search_query: Optional[str]# Última búsqueda realizada (None si no ha buscado nada)
    last_search_filters: Optional[dict] = None  # Últimos filtros aplicados
    last_results: List[Any]         # Últimos resultados guardados (tipo genérico)
    searches_count: int             # Número total de búsquedas realizadas por el usuario