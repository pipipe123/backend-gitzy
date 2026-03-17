"""
request_models.py - Modelos de entrada (Request Models)

Define la estructura de los datos que recibe la API desde el cliente.
Pydantic valida automáticamente que los datos cumplan con el formato esperado.

Si los datos no son válidos, FastAPI devuelve error 422 (Unprocessable Entity)
con detalles de qué campos están incorrectos.
"""

# BaseModel: Clase base de Pydantic para crear modelos de datos con validación
# HttpUrl: Tipo especial que valida que una string sea una URL válida
from pydantic import BaseModel, HttpUrl, model_validator

from typing import Optional
from enum import Enum


# Lenguajes de programación soportados para el filtro
class ProgrammingLanguage(str, Enum):
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    TYPESCRIPT = "TypeScript"
    JAVA = "Java"
    GO = "Go"
    RUST = "Rust"
    CPP = "C++"
    C = "C"
    CSHARP = "C#"
    RUBY = "Ruby"
    PHP = "PHP"
    SWIFT = "Swift"
    KOTLIN = "Kotlin"


# Categorías fijas de tipo de proyecto
class ProjectCategory(str, Enum):
    LIBRARY = "Library"
    FRAMEWORK = "Framework"
    APPLICATION = "Application"
    TOOL = "Tool"
    API = "API"


# Mapeo de categoría a topic usado en GitHub/GitLab
CATEGORY_TO_TOPICS = {
    ProjectCategory.LIBRARY: "library",
    ProjectCategory.FRAMEWORK: "framework",
    ProjectCategory.APPLICATION: "application",
    ProjectCategory.TOOL: "tool",
    ProjectCategory.API: "api",
}


class Provider(str, Enum):
    GITHUB = "GitHub"
    GITLAB = "GitLab"
    AZURE = "Azure"


class SearchFilters(BaseModel):
    """Filtros opcionales de búsqueda. Máximo 3 filtros activos a la vez."""
    language: Optional[ProgrammingLanguage] = None
    category: Optional[ProjectCategory] = None
    topic: Optional[str] = None
    provider: Optional[Provider] = None

    @model_validator(mode="after")#hace que primero cuente los filtros
    def validate_max_filters(self):
        active = sum(1 for v in [self.language, self.category, self.topic] if v is not None)
        if active > 3:
            raise ValueError("Máximo 3 filtros pueden aplicarse al mismo tiempo")
        return self


# Modelo para el endpoint POST /repository/analyze
# Valida que el usuario envíe una URL válida de repositorio
class RepositoryAnalyzeRequest(BaseModel):
    # Campo 'url' debe ser una URL HTTP/HTTPS válida
    # Pydantic valida automáticamente el formato
    # ✅ Válido: "https://github.com/user/repo"
    # ❌ Inválido: "no-es-una-url", "github.com" (sin protocolo)
    url: HttpUrl  # esto valida que lo que reciba sea una url


# Modelo para los endpoints POST /repository/file/content y /file/download
# Valida URL del repositorio + ruta del archivo
class FileContentRequest(BaseModel):
    url: HttpUrl          # URL del repositorio (ej: "https://github.com/user/repo")
    path: str             # Ruta del archivo dentro del repo (ej: "src/main.py")
    ref: Optional[str] = None  # Branch o commit (opcional, usa default_branch si es None)

    @model_validator(mode="after")
    def clean_ref(self):
        if self.ref in (None, "", "string"):
            self.ref = None
        return self


# Modelo para el endpoint POST /repository/metrics
class MetricsRequest(BaseModel):
    url: HttpUrl
    max_files: int = 30


# Modelo para el endpoint POST /repository/search
# Valida que el usuario envíe un texto de búsqueda
class SearchRequest(BaseModel):
    # Campo 'query' es una string con el texto a buscar
    # Ejemplo: "fastapi", "react", "machine learning"
    # Pydantic valida que sea string (no número, no null, etc.)
    query: str  # Texto de búsqueda
    filters: Optional[SearchFilters] = None  # Filtros opcionales
