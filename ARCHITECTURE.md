# 📐 Arquitectura del Proyecto - Repository Analyzer API

## 📂 Estructura de Carpetas

```
backend/
├── app/
│   ├── __init__.py                    # Marca app como paquete Python
│   ├── main.py                        # ⭐ Punto de entrada de la aplicación
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                  # Configuración global y variables de entorno
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request_models.py          # Modelos de datos de entrada (requests)
│   │   └── response_models.py         # Modelos de datos de salida (responses)
│   ├── routers/
│   │   ├── __init__.py
│   │   └── repository.py              # ⭐ Endpoints de la API (rutas)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── session_service.py         # Gestión de sesiones y cookies
│   │   ├── github_service.py          # Análisis detallado de repositorios GitHub
│   │   ├── github_search_service.py   # Búsqueda de repositorios en GitHub
│   │   ├── gitlab_service.py          # Búsqueda de repositorios en GitLab
│   │   ├── azure_service.py           # Búsqueda de repositorios en Azure DevOps
│   │   └── provider_detector.py       # Detecta el proveedor por URL
│   └── utils/
│       ├── __init__.py
│       └── http_client.py             # Cliente HTTP asíncrono compartido
├── .env                               # Variables de entorno (tokens, secrets)
├── .env.example                       # Ejemplo de configuración
├── requeriments.text                  # Dependencias de Python
└── README.md                          # Documentación de uso
```

---

## 🔄 Flujo de la Aplicación

```
1. Usuario hace request →
2. main.py (FastAPI) →
3. CORS Middleware (valida origen) →
4. repository.py (router/endpoint) →
5. Verifica/crea cookie de sesión →
6. Llama a servicios de búsqueda (GitHub/GitLab/Azure) →
7. http_client.py hace peticiones HTTP →
8. Respuestas se combinan y formatean →
9. session_service.py guarda en sesión →
10. Respuesta JSON + Cookie al usuario
```

---

## 📄 Análisis Línea por Línea

### 🟢 `app/main.py` - Punto de Entrada

**Función en el flujo:** Inicializa la aplicación FastAPI, configura CORS y registra routers.

```python
# Línea 1: Importa la clase FastAPI, el framework web que usamos
from fastapi import FastAPI

# Línea 2: Importa el middleware de CORS para permitir peticiones cross-origin
from fastapi.middleware.cors import CORSMiddleware

# Línea 3: Importa nuestro router de repository que contiene todos los endpoints
from app.routers import repository

# Líneas 5-9: Crea la instancia principal de la aplicación FastAPI
app = FastAPI(
    title="Repository Analyzer API",  # Nombre que aparece en la documentación
    version="1.0.0",  # Versión de la API
    description="API para buscar repositorios en GitHub, GitLab y Azure DevOps con persistencia de sesión"
)

# Líneas 11-18: Configuración del middleware CORS
# CORS = Cross-Origin Resource Sharing (permite que el frontend acceda al backend)
app.add_middleware(
    CORSMiddleware,
    # allow_origins: Lista de dominios que pueden hacer peticiones
    # Aquí ponemos localhost:3000 (React) y localhost:5173 (Vite)
    allow_origins=["http://localhost:3000", "http://localhost:5173"],

    # allow_credentials: DEBE ser True para que las cookies funcionen
    # Sin esto, el navegador bloqueará las cookies en peticiones cross-origin
    allow_credentials=True,

    # allow_methods: Permite todos los métodos HTTP (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],

    # allow_headers: Permite todos los headers HTTP
    allow_headers=["*"],
)

# Línea 20: Registra el router de repository con todos sus endpoints
# Esto hace que todos los endpoints definidos en repository.py estén disponibles
app.include_router(repository.router)
```

**¿Qué hace este archivo?**
- Crea la aplicación FastAPI
- Configura CORS para permitir cookies desde el frontend
- Conecta los routers (endpoints) a la aplicación

---

### 🟢 `app/core/config.py` - Configuración Global

**Función en el flujo:** Centraliza todas las configuraciones y variables de entorno.

```python
# Línea 1: Módulo para interactuar con el sistema operativo (leer variables de entorno)
import os

# Línea 2: Librería para cargar variables desde el archivo .env
from dotenv import load_dotenv

# Línea 4: Ejecuta la carga del archivo .env
# Esto hace que las variables definidas en .env estén disponibles con os.getenv()
load_dotenv()

# Líneas 6-16: Clase que contiene toda la configuración de la aplicación
class Settings:
    # Línea 7: Token de GitHub para autenticar peticiones a la API de GitHub
    # os.getenv("GITHUB_TOKEN") lee la variable GITHUB_TOKEN del .env
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN")

    # Línea 8: Token de GitLab (opcional, por eso tiene default "")
    GITLAB_TOKEN: str = os.getenv("GITLAB_TOKEN", "")

    # Línea 9: Token de Azure DevOps (opcional)
    AZURE_TOKEN: str = os.getenv("AZURE_TOKEN", "")

    # Línea 11: Clave secreta para firmar cookies
    # En producción DEBE cambiarse por algo seguro y aleatorio
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu-secreto-super-seguro-cambialo-en-produccion")

    # Línea 13: Nombre de la cookie que se enviará al navegador
    COOKIE_NAME: str = "session_id"

    # Línea 14: Tiempo de vida de la cookie en segundos
    # 30 días * 24 horas * 60 minutos * 60 segundos = 2,592,000 segundos
    COOKIE_MAX_AGE: int = 30 * 24 * 60 * 60

# Línea 16: Crea una instancia única (singleton) de Settings
# Todos los demás archivos importarán esta instancia
settings = Settings()
```

**¿Qué hace este archivo?**
- Carga variables de entorno desde `.env`
- Define configuraciones de tokens de API
- Define configuración de cookies (nombre, duración, secret)
- Exporta una instancia `settings` usada en toda la app

---

### 🟢 `app/models/request_models.py` - Modelos de Entrada

**Función en el flujo:** Define la estructura de los datos que recibe la API.

```python
# Línea 1: BaseModel es la clase base de Pydantic para crear modelos de datos
# HttpUrl es un tipo especial que valida URLs
from pydantic import BaseModel, HttpUrl

# Líneas 3-4: Modelo para el endpoint de análisis de repositorio
class RepositoryAnalyzeRequest(BaseModel):
    # url debe ser una URL válida (Pydantic valida automáticamente el formato)
    # Si el usuario envía algo que no es una URL válida, Pydantic devuelve error 422
    url: HttpUrl  # esto valida que lo que reciba sea una url


# Líneas 7-8: Modelo para el endpoint de búsqueda
class SearchRequest(BaseModel):
    # query es un string simple con el texto de búsqueda
    # Ejemplo: "fastapi", "react", "machine learning"
    query: str  # Texto de búsqueda
```

**¿Qué hace este archivo?**
- Define modelos Pydantic para validar datos de entrada
- `RepositoryAnalyzeRequest`: valida URLs de repositorios
- `SearchRequest`: valida texto de búsqueda
- Pydantic automáticamente valida tipos y devuelve errores descriptivos

---

### 🟢 `app/models/response_models.py` - Modelos de Salida

**Función en el flujo:** Define la estructura de las respuestas JSON de la API.

```python
# Línea 1: Importa BaseModel y tipos de Python para validación
from pydantic import BaseModel
from typing import List, Optional, Any


# Líneas 5-8: Modelo para un commit de Git
class Commit(BaseModel):
    sha: str           # Hash único del commit (ej: "a3f2c1...")
    message: str       # Mensaje del commit
    author: Optional[str]  # Nombre del autor (puede ser None)


# Líneas 11-25: Modelo para la respuesta completa de análisis de repositorio
class RepositoryResponse(BaseModel):
    provider: str              # "github", "gitlab" o "azure"
    name: str                  # Nombre del repositorio
    owner: str                 # Usuario o organización dueña
    description: Optional[str] # Descripción (puede ser None)
    is_private: bool           # True si es privado
    default_branch: str        # Rama principal (ej: "main" o "master")
    created_at: str            # Fecha de creación (formato ISO)
    updated_at: str            # Fecha de última actualización
    stars: int                 # Número de estrellas
    forks: int                 # Número de forks
    open_issues: int           # Issues abiertos
    languages: List[str]       # Lista de lenguajes (ej: ["Python", "JavaScript"])
    commits: List[Commit]      # Lista de últimos commits
    url: str                   # URL del repositorio


# Líneas 28-36: Modelo para un resultado individual de búsqueda
class SearchResultItem(BaseModel):
    provider: str              # Proveedor: "github", "gitlab", "azure"
    name: str                  # Nombre del repo
    owner: str                 # Dueño del repo
    description: Optional[str] # Descripción (puede ser None)
    url: str                   # URL al repositorio
    stars: int                 # Número de estrellas
    language: Optional[str]    # Lenguaje principal (puede ser None)
    updated_at: str            # Última actualización


# Líneas 39-42: Modelo para la respuesta de búsqueda completa
class SearchResponse(BaseModel):
    query: str                      # Texto que se buscó
    results: List[SearchResultItem] # Lista de resultados encontrados
    total_results: int              # Número total de resultados


# Líneas 45-49: Modelo para la respuesta de datos de sesión
class SessionResponse(BaseModel):
    session_id: str                 # UUID de la sesión
    last_search_query: Optional[str]# Última búsqueda realizada (puede ser None)
    last_results: List[Any]         # Últimos resultados (tipo genérico)
    searches_count: int             # Número total de búsquedas realizadas
```

**¿Qué hace este archivo?**
- Define modelos Pydantic para las respuestas de la API
- FastAPI usa estos modelos para:
  - Validar que las respuestas tengan la estructura correcta
  - Generar documentación automática (Swagger)
  - Serializar datos a JSON

---

### 🟢 `app/routers/repository.py` - Endpoints de la API

**Función en el flujo:** Define las rutas HTTP y la lógica de cada endpoint.

```python
# Líneas 1-2: Importaciones de FastAPI
# APIRouter: para crear grupos de rutas
# HTTPException: para devolver errores HTTP
# Response: para modificar la respuesta (agregar cookies)
# Cookie: para leer cookies de las peticiones
from fastapi import APIRouter, HTTPException, Response, Cookie
from typing import Optional

# Líneas 3-9: Importa todos los modelos de request y response
from app.models.request_models import RepositoryAnalyzeRequest, SearchRequest
from app.models.response_models import (
    RepositoryResponse,
    SearchResponse,
    SessionResponse,
    SearchResultItem
)

# Líneas 10-19: Importa todos los servicios necesarios
from app.services.provider_detector import detect_provider
from app.services.github_service import get_github_repository
from app.services.github_search_service import search_github_repositories
from app.services.gitlab_service import search_gitlab_repositories
from app.services.azure_service import search_azure_repositories
from app.services.session_service import (
    create_session,      # Crea una nueva sesión
    get_session,         # Obtiene datos de una sesión
    save_search_to_session  # Guarda búsqueda en sesión
)
from app.core.config import settings

# Líneas 22-25: Crea un router con prefijo y etiqueta
router = APIRouter(
    prefix="/repository",  # Todas las rutas empezarán con /repository
    tags=["Repository"]    # Agrupa endpoints en la documentación
)


# Líneas 28-68: ENDPOINT PRINCIPAL - Búsqueda de repositorios
@router.post("/search", response_model=SearchResponse)
async def search_repositories(
    request: SearchRequest,  # Body del POST (contiene "query")
    response: Response,      # Objeto para modificar la respuesta (agregar cookies)
    # Lee la cookie session_id si existe, si no existe es None
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME)
):
    """
    Busca repositorios en GitHub, GitLab y Azure DevOps.
    Guarda los resultados en la sesión del usuario mediante cookies.
    """
    # Líneas 39-48: Manejo de sesión
    # Si no hay cookie O la sesión no existe en memoria
    if not session_id or not get_session(session_id):
        # Crea una nueva sesión (genera UUID único)
        session_id = create_session()

        # Establece la cookie en la respuesta HTTP
        response.set_cookie(
            key=settings.COOKIE_NAME,    # Nombre: "session_id"
            value=session_id,             # Valor: UUID generado
            max_age=settings.COOKIE_MAX_AGE,  # Duración: 30 días
            httponly=True,                # No accesible por JavaScript (seguridad)
            samesite="lax"                # Protección CSRF moderada
        )

    # Líneas 50-53: Búsqueda paralela en todos los proveedores
    # await: espera a que cada función asíncrona termine
    # Estas 3 búsquedas se ejecutan al mismo tiempo (concurrencia)
    github_results = await search_github_repositories(request.query)
    gitlab_results = await search_gitlab_repositories(request.query)
    azure_results = await search_azure_repositories(request.query)

    # Línea 55-56: Combina todos los resultados en una sola lista
    all_results = github_results + gitlab_results + azure_results

    # Línea 58-59: Convierte diccionarios a objetos Pydantic
    # SearchResultItem(**item) desempaqueta el dict y crea el modelo
    search_items = [SearchResultItem(**item) for item in all_results]

    # Línea 61-62: Guarda la búsqueda en la sesión del usuario
    save_search_to_session(session_id, request.query, all_results)

    # Líneas 64-68: Retorna la respuesta
    return SearchResponse(
        query=request.query,      # Texto que se buscó
        results=search_items,     # Lista de repositorios encontrados
        total_results=len(search_items)  # Cantidad total
    )


# Líneas 71-98: ENDPOINT - Recuperar datos de sesión
@router.get("/session", response_model=SessionResponse)
async def get_session_data(
    response: Response,
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME)
):
    """
    Recupera los datos de la sesión del usuario.
    Si no hay sesión, crea una nueva.
    """
    # Líneas 80-89: Verifica si existe sesión
    if not session_id or not get_session(session_id):
        # No hay sesión → crear una nueva
        session_id = create_session()
        response.set_cookie(
            key=settings.COOKIE_NAME,
            value=session_id,
            max_age=settings.COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax"
        )
        session_data = get_session(session_id)
    else:
        # Ya hay sesión → obtener sus datos
        session_data = get_session(session_id)

    # Líneas 93-98: Retorna los datos de la sesión
    return SessionResponse(
        session_id=session_id,
        last_search_query=session_data.get("last_search_query"),
        last_results=session_data.get("last_results", []),
        searches_count=len(session_data.get("searches", []))
    )


# Líneas 101-120: ENDPOINT - Analizar repositorio específico por URL
@router.post("/analyze", response_model=RepositoryResponse)
async def analyze_repository(request: RepositoryAnalyzeRequest):
    """Analiza un repositorio específico de GitHub por URL"""
    # Línea 104: Detecta el proveedor y extrae owner/repo de la URL
    provider, repo_info = detect_provider(str(request.url))

    # Líneas 106-110: Valida que la URL sea soportada
    if not provider:
        raise HTTPException(
            status_code=400,
            detail="URL no soportada. Solo se admiten repositorios de GitHub."
        )

    # Líneas 112-120: Si es GitHub, obtiene información detallada
    if provider == "github":
        try:
            data = await get_github_repository(repo_info)
            return data
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al analizar el repositorio: {str(e)}"
            )
```

**¿Qué hace este archivo?**
- Define 3 endpoints principales:
  1. `POST /repository/search`: Busca repos en GitHub/GitLab/Azure
  2. `GET /repository/session`: Obtiene datos guardados del usuario
  3. `POST /repository/analyze`: Analiza un repo específico por URL
- Maneja cookies de sesión automáticamente
- Coordina llamadas a servicios externos

---

### 🟢 `app/services/session_service.py` - Gestión de Sesiones

**Función en el flujo:** Gestiona el almacenamiento y recuperación de sesiones de usuario.

```python
# Línea 1: uuid genera identificadores únicos universales
import uuid
# Línea 2: Dict y Any son tipos de Python para anotaciones
from typing import Dict, Any, Optional
# Línea 3: datetime para manejar fechas y horas
from datetime import datetime


# Líneas 6-7: Almacén en memoria de todas las sesiones
# Estructura: { "uuid-session-1": {...datos...}, "uuid-session-2": {...datos...} }
# ⚠️ IMPORTANTE: Esto se pierde al reiniciar el servidor
# En producción usar Redis o base de datos
sessions_store: Dict[str, Dict[str, Any]] = {}


# Líneas 10-22: Función para crear una nueva sesión
def create_session() -> str:
    """Crea una nueva sesión y retorna el ID"""
    # Línea 13: Genera un UUID único (ej: "a3f2c1b4-...")
    session_id = str(uuid.uuid4())

    # Líneas 14-21: Inicializa los datos de la sesión
    sessions_store[session_id] = {
        "created_at": datetime.now().isoformat(),  # Fecha de creación
        "last_accessed": datetime.now().isoformat(),  # Último acceso
        "searches": [],          # Lista de búsquedas realizadas
        "last_search_query": None,  # Última búsqueda (None al inicio)
        "last_results": []       # Últimos resultados (vacío al inicio)
    }
    # Línea 22: Retorna el UUID de la sesión creada
    return session_id


# Líneas 25-30: Función para obtener datos de una sesión
def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene los datos de una sesión"""
    # Línea 27: Verifica si el session_id existe en el diccionario
    if session_id in sessions_store:
        # Actualiza el timestamp de último acceso
        sessions_store[session_id]["last_accessed"] = datetime.now().isoformat()
        # Retorna todos los datos de la sesión
        return sessions_store[session_id]
    # Si no existe, retorna None
    return None


# Líneas 33-37: Función para actualizar datos de una sesión
def update_session(session_id: str, data: Dict[str, Any]) -> None:
    """Actualiza los datos de una sesión"""
    if session_id in sessions_store:
        # .update() fusiona el nuevo diccionario con el existente
        sessions_store[session_id].update(data)
        # Actualiza timestamp de último acceso
        sessions_store[session_id]["last_accessed"] = datetime.now().isoformat()


# Líneas 40-55: Función para guardar una búsqueda en la sesión
def save_search_to_session(session_id: str, query: str, results: list) -> None:
    """Guarda una búsqueda en la sesión del usuario"""
    if session_id in sessions_store:
        # Línea 43: Obtiene referencia a los datos de la sesión
        session = sessions_store[session_id]

        # Líneas 45-50: Agrega la búsqueda al historial
        session["searches"].append({
            "query": query,  # Texto buscado
            "timestamp": datetime.now().isoformat(),  # Cuándo se buscó
            "results_count": len(results)  # Cuántos resultados se encontraron
        })

        # Líneas 52-54: Guarda como "última búsqueda" para acceso rápido
        session["last_search_query"] = query
        session["last_results"] = results
        session["last_accessed"] = datetime.now().isoformat()
```

**¿Qué hace este archivo?**
- Gestiona sesiones en memoria (diccionario Python)
- `create_session()`: genera UUID único para nueva sesión
- `get_session()`: recupera datos de una sesión existente
- `save_search_to_session()`: guarda búsquedas y resultados
- ⚠️ Las sesiones se pierden al reiniciar (usar Redis en producción)

---

### 🟢 `app/services/github_search_service.py` - Búsqueda en GitHub

**Función en el flujo:** Busca repositorios en GitHub usando su API de búsqueda.

```python
# Líneas 1-2: Importa configuración y cliente HTTP
from app.core.config import settings
from app.utils.http_client import get


# Líneas 5-48: Función asíncrona para buscar en GitHub
async def search_github_repositories(query: str):
    """Busca repositorios en GitHub"""
    # Líneas 7-9: Configura headers HTTP para la petición
    headers = {
        "Accept": "application/vnd.github+json"  # Header requerido por GitHub API
    }

    # Líneas 11-12: Si hay token, agrégalo para más rate limit
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    # Líneas 14-15: Construye la URL de búsqueda
    # q= texto de búsqueda
    # sort=stars ordena por más estrellas
    # per_page=10 limita a 10 resultados
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=10"

    # Líneas 17-48: Try-catch para manejar errores
    try:
        # Línea 18: Hace la petición HTTP GET asíncrona
        response = await get(url, headers)

        # Líneas 19-20: Si hay error, retorna lista vacía
        if response.status_code != 200:
            return []

        # Línea 22: Parsea el JSON de la respuesta
        data = response.json()
        # Línea 23: Inicializa lista de resultados
        results = []

        # Líneas 25-37: Itera sobre cada repositorio encontrado
        for repo in data.get("items", []):
            # Agrega un diccionario con los datos importantes
            results.append({
                "provider": "github",  # Identifica el proveedor
                "name": repo.get("name", ""),  # Nombre del repo
                "owner": repo.get("owner", {}).get("login", ""),  # Dueño
                "description": repo.get("description"),  # Descripción
                "url": repo.get("html_url", ""),  # URL del repo
                "stars": repo.get("stargazers_count", 0),  # Estrellas
                "language": repo.get("language"),  # Lenguaje principal
                "updated_at": repo.get("updated_at", "")  # Última actualización
            })

        # Línea 39: Retorna la lista de resultados
        return results

    # Líneas 40-42: Si hay error, imprime y retorna vacío
    except Exception as e:
        print(f"Error buscando en GitHub: {str(e)}")
        return []
```

**¿Qué hace este archivo?**
- Busca repositorios en GitHub usando su API REST
- Ordena resultados por número de estrellas
- Maneja autenticación con token (opcional)
- Formatea respuesta a estructura estándar
- Maneja errores devolviendo lista vacía

---

### 🟢 `app/services/gitlab_service.py` - Búsqueda en GitLab

**Función en el flujo:** Busca repositorios (proyectos) en GitLab.

```python
from app.core.config import settings
from app.utils.http_client import get


async def search_gitlab_repositories(query: str):
    """Busca repositorios en GitLab"""
    # Línea 7: Inicializa headers vacío
    headers = {}

    # Líneas 8-9: Si hay token de GitLab, agrégalo
    # GitLab usa "PRIVATE-TOKEN" en vez de "Authorization"
    if settings.GITLAB_TOKEN:
        headers["PRIVATE-TOKEN"] = settings.GITLAB_TOKEN

    # Líneas 11-12: URL de búsqueda de GitLab
    # search= texto a buscar
    # per_page=10 limita resultados
    # order_by=stars ordena por estrellas
    url = f"https://gitlab.com/api/v4/projects?search={query}&per_page=10&order_by=stars"

    try:
        # Línea 15: Hace petición GET (headers solo si hay token)
        response = await get(url, headers if headers else None)

        # Líneas 16-17: Si hay error, retorna vacío
        if response.status_code != 200:
            return []

        # Línea 19: Parsea JSON
        projects = response.json()
        # Línea 20: Inicializa resultados
        results = []

        # Líneas 22-33: Procesa cada proyecto encontrado
        for project in projects:
            results.append({
                "provider": "gitlab",  # Identifica como GitLab
                "name": project.get("name", ""),
                # namespace es el dueño en GitLab
                "owner": project.get("namespace", {}).get("name", ""),
                "description": project.get("description"),
                "url": project.get("web_url", ""),
                "stars": project.get("star_count", 0),
                # GitLab API de búsqueda no devuelve lenguaje principal
                "language": None,
                "updated_at": project.get("last_activity_at", "")
            })

        # Línea 35: Retorna resultados
        return results

    # Líneas 36-38: Manejo de errores
    except Exception as e:
        print(f"Error buscando en GitLab: {str(e)}")
        return []
```

**¿Qué hace este archivo?**
- Busca proyectos en GitLab usando su API v4
- Usa token opcional para mayor rate limit
- Formatea respuesta al formato estándar
- `language` es None (API de búsqueda no lo incluye)

---

### 🟢 `app/services/azure_service.py` - Búsqueda en Azure DevOps

**Función en el flujo:** Preparado para buscar en Azure DevOps (requiere configuración adicional).

```python
from app.core.config import settings
from app.utils.http_client import get


async def search_azure_repositories(query: str):
    """Busca repositorios en Azure DevOps"""
    # Líneas 6-7: Azure DevOps requiere token obligatorio
    if not settings.AZURE_TOKEN:
        return []  # Sin token, no puede buscar

    # Líneas 9-13: Azure DevOps usa autenticación Basic
    headers = {
        "Authorization": f"Basic {settings.AZURE_TOKEN}",
        "Content-Type": "application/json"
    }

    # Líneas 15-23: Nota sobre Azure DevOps
    # Azure requiere especificar una ORGANIZACIÓN específica
    # No tiene endpoint global de búsqueda como GitHub/GitLab
    # Requiere configuración adicional por organización
    try:
        # Por ahora retorna vacío
        # Aquí iría la lógica específica con org configurada
        return []

    except Exception as e:
        print(f"Error buscando en Azure DevOps: {str(e)}")
        return []
```

**¿Qué hace este archivo?**
- Placeholder para Azure DevOps
- Azure requiere configuración de organización específica
- No tiene API de búsqueda global como GitHub/GitLab
- Retorna vacío por ahora (requiere implementación custom)

---

### 🟢 `app/services/github_service.py` - Análisis Detallado de Repositorio

**Función en el flujo:** Obtiene información detallada de un repositorio específico de GitHub.

```python
from app.core.config import settings
from app.utils.http_client import get


async def get_github_repository(repo_info: dict):
    # Líneas 6-7: Extrae owner y repo del diccionario
    # Ejemplo: {"owner": "tiangolo", "repo": "fastapi"}
    owner = repo_info["owner"]
    repo = repo_info["repo"]

    # Líneas 9-13: Configura headers con token
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # Línea 15: URL base del repositorio
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    # Líneas 17-22: Obtiene información general del repositorio
    repo_response = await get(base_url, headers)
    if repo_response.status_code != 200:
        raise Exception("Error obteniendo información del repositorio")

    repo_data = repo_response.json()

    # Líneas 24-27: Obtiene lenguajes usados en el repositorio
    languages_response = await get(f"{base_url}/languages", headers)
    languages_data = languages_response.json()
    # Convierte dict de lenguajes a lista de nombres
    # {"Python": 50000, "JavaScript": 3000} → ["Python", "JavaScript"]
    languages = list(languages_data.keys())

    # Líneas 29-31: Obtiene últimos 5 commits
    commits_response = await get(f"{base_url}/commits?per_page=5", headers)
    commits_data = commits_response.json()

    # Líneas 33-40: Procesa commits
    commits = []
    for commit in commits_data:
        commits.append({
            "sha": commit["sha"],  # Hash del commit
            "message": commit["commit"]["message"],  # Mensaje
            "author": commit["commit"]["author"]["name"]  # Autor
        })

    # Líneas 42-58: Retorna diccionario con toda la información
    return {
        "provider": "github",
        "name": repo_data["name"],
        "owner": repo_data["owner"]["login"],
        "description": repo_data["description"],
        "is_private": repo_data["private"],
        "default_branch": repo_data["default_branch"],
        "created_at": repo_data["created_at"],
        "updated_at": repo_data["updated_at"],
        "stars": repo_data["stargazers_count"],
        "forks": repo_data["forks_count"],
        "open_issues": repo_data["open_issues_count"],
        "languages": languages,  # Lista de lenguajes
        "commits": commits,  # Lista de últimos commits
        "url": repo_data["html_url"]
    }
```

**¿Qué hace este archivo?**
- Obtiene información DETALLADA de un repositorio específico
- Hace 3 peticiones a GitHub API:
  1. Info general del repo
  2. Lenguajes usados
  3. Últimos 5 commits
- Combina toda la información en una respuesta completa

---

### 🟢 `app/services/provider_detector.py` - Detector de Proveedor

**Función en el flujo:** Detecta si una URL es de GitHub/GitLab/Azure y extrae owner/repo.

```python
# Línea 1: urlparse descompone una URL en sus partes
from urllib.parse import urlparse

def detect_provider(url: str):
    # Línea 4: Parsea la URL
    # "https://github.com/owner/repo" →
    # parsed.netloc = "github.com"
    # parsed.path = "/owner/repo"
    parsed = urlparse(url)

    # Líneas 6-12: Detecta si es GitHub
    if "github.com" in parsed.netloc:
        # Línea 7: Divide el path en partes
        # "/owner/repo" → ["owner", "repo"]
        # .strip("/") quita las barras de los extremos
        # .split("/") divide por barras
        parts = parsed.path.strip("/").split("/")

        # Línea 8: Verifica que haya al menos owner y repo
        if len(parts) >= 2:
            # Línea 9-12: Retorna proveedor e info
            return "github", {
                "owner": parts[0],  # Primera parte = owner
                "repo": parts[1]    # Segunda parte = repo
            }

    # Línea 13: Si no es GitHub (o faltan partes), retorna None
    return None, None
```

**¿Qué hace este archivo?**
- Parsea URLs de repositorios
- Detecta si es GitHub (extensible a GitLab/Azure)
- Extrae owner y nombre del repositorio
- Retorna tupla: `(proveedor, {owner, repo})`

---

### 🟢 `app/utils/http_client.py` - Cliente HTTP

**Función en el flujo:** Cliente HTTP asíncrono reutilizable para todas las peticiones.

```python
# Línea 1: httpx es una librería HTTP moderna con soporte async
import httpx


# Líneas 4-8: Función asíncrona genérica para GET
async def get(url: str, headers: dict = None):
    """Cliente HTTP para realizar peticiones GET asíncronas"""
    # Línea 7: Crea un cliente HTTP asíncrono
    # async with: se asegura que el cliente se cierre al terminar
    async with httpx.AsyncClient() as client:
        # Línea 8: Hace petición GET y espera respuesta
        # await: espera la respuesta sin bloquear el servidor
        response = await client.get(url, headers=headers)
        # Retorna el objeto Response de httpx
        return response
```

**¿Qué hace este archivo?**
- Wrapper simple sobre httpx
- Peticiones GET asíncronas
- Maneja la creación y cierre del cliente automáticamente
- Reutilizable en todos los servicios

---

## 🔄 Flujo Completo: Usuario Busca "fastapi"

### 1️⃣ Frontend hace petición
```javascript
fetch('http://localhost:8000/repository/search', {
  method: 'POST',
  credentials: 'include',  // ← Envía/recibe cookies
  body: JSON.stringify({ query: 'fastapi' })
})
```

### 2️⃣ FastAPI recibe la petición
- `main.py` → Middleware CORS valida origen
- `main.py` → Enruta a `repository.router`

### 3️⃣ Router procesa la petición
- `repository.py` → Endpoint `search_repositories()`
- Lee cookie `session_id` del header (si existe)

### 4️⃣ Gestión de sesión
- `session_service.py` → `get_session(session_id)`
- Si no existe → `create_session()` → genera UUID
- `repository.py` → `response.set_cookie()` → envía cookie

### 5️⃣ Búsqueda paralela
- `github_search_service.py` → busca en GitHub
- `gitlab_service.py` → busca en GitLab
- `azure_service.py` → (retorna vacío por ahora)

### 6️⃣ Cada servicio hace peticiones HTTP
- `http_client.py` → `get(url, headers)`
- `httpx.AsyncClient()` → petición HTTP real
- APIs externas responden con JSON

### 7️⃣ Procesar resultados
- `repository.py` → combina todos los resultados
- Convierte a modelos Pydantic `SearchResultItem`
- `session_service.py` → guarda en memoria

### 8️⃣ Respuesta al usuario
- `repository.py` → retorna `SearchResponse`
- FastAPI serializa a JSON
- Headers incluyen `Set-Cookie: session_id=...`

### 9️⃣ Navegador guarda cookie
- Próxima petición incluirá automáticamente la cookie
- Backend recuperará sesión guardada

---

## 🎯 Conceptos Clave

### Cookies
```python
# Crear cookie
response.set_cookie(
    key="session_id",        # Nombre
    value="uuid-aqui",       # Valor único
    max_age=2592000,         # 30 días
    httponly=True,           # No accesible por JS
    samesite="lax"           # Protección CSRF
)

# Leer cookie
session_id: str = Cookie(None, alias="session_id")
```

### Async/Await
```python
# Función asíncrona (no bloquea)
async def buscar():
    # Espera sin bloquear el servidor
    resultado = await hacer_peticion()
    return resultado

# Múltiples peticiones paralelas
github = await search_github()  # Espera
gitlab = await search_gitlab()  # Espera
# Total: tiempo del más lento (no suma)
```

### Pydantic Validation
```python
class SearchRequest(BaseModel):
    query: str  # Valida que sea string

# Si envían: {"query": 123}
# Pydantic auto-convierte: "123"

# Si envían: {"otra_cosa": "x"}
# Pydantic rechaza: 422 Unprocessable Entity
```

---

## 📚 Resumen por Capas

| Capa | Archivos | Responsabilidad |
|------|----------|----------------|
| **Entrada** | `main.py` | Inicializa app, CORS |
| **Rutas** | `routers/repository.py` | Define endpoints HTTP |
| **Validación** | `models/*.py` | Valida entrada/salida |
| **Lógica** | `services/*.py` | Búsqueda, sesiones |
| **Infraestructura** | `utils/http_client.py` | Cliente HTTP |
| **Configuración** | `core/config.py` | Tokens, settings |

---

## 🔒 Seguridad

### ✅ Buenas prácticas implementadas
- **httponly=True**: JS no puede acceder a cookies
- **samesite=lax**: Protección básica CSRF
- **CORS configurado**: Solo orígenes permitidos
- **Tokens en .env**: No hardcodeados

### ⚠️ Para producción
- Cambiar `SECRET_KEY` a valor aleatorio fuerte
- Usar `samesite="strict"` si es posible
- Agregar HTTPS (`secure=True` en cookies)
- Migrar sesiones de memoria a Redis/DB
- Agregar rate limiting
- Agregar expiración de sesiones viejas

---

¿Quieres que profundice en alguna sección específica?
