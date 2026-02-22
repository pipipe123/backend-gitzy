"""
request_models.py - Modelos de entrada (Request Models)

Define la estructura de los datos que recibe la API desde el cliente.
Pydantic valida automáticamente que los datos cumplan con el formato esperado.

Si los datos no son válidos, FastAPI devuelve error 422 (Unprocessable Entity)
con detalles de qué campos están incorrectos.
"""

# BaseModel: Clase base de Pydantic para crear modelos de datos con validación
# HttpUrl: Tipo especial que valida que una string sea una URL válida
from pydantic import BaseModel, HttpUrl

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