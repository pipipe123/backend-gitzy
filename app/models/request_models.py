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


class SearchFilters(BaseModel):
    """Filtros opcionales de búsqueda. Máximo 3 filtros activos a la vez."""
    language: Optional[ProgrammingLanguage] = None
    category: Optional[ProjectCategory] = None
    topic: Optional[str] = None

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


# Modelo para el endpoint POST /repository/search
# Valida que el usuario envíe un texto de búsqueda
class SearchRequest(BaseModel):
    # Campo 'query' es una string con el texto a buscar
    # Ejemplo: "fastapi", "react", "machine learning"
    # Pydantic valida que sea string (no número, no null, etc.)
    query: str  # Texto de búsqueda
    filters: Optional[SearchFilters] = None  # Filtros opcionales
