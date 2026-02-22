"""
repository.py - Router con todos los endpoints de la API

Este es el archivo MÁS IMPORTANTE del backend.
Define los 3 endpoints principales:
1. POST /repository/search - Busca repos en GitHub/GitLab/Azure
2. GET /repository/session - Obtiene datos guardados del usuario
3. POST /repository/analyze - Analiza un repo específico por URL

También maneja TODA la lógica de cookies de sesión.

Flujo típico:
1. Usuario hace request → FastAPI → repository.py
2. Lee cookie de sesión (si existe)
3. Crea nueva sesión si no existe (genera UUID)
4. Establece cookie en la respuesta
5. Ejecuta búsqueda/análisis
6. Guarda resultados en sesión
7. Devuelve JSON + cookie al usuario
"""

# --- Importaciones de FastAPI ---
# APIRouter: Crea un grupo de rutas relacionadas (prefix=/repository)
from fastapi import APIRouter

# HTTPException: Para devolver errores HTTP con código y mensaje
from fastapi import HTTPException

# Response: Objeto para modificar la respuesta HTTP (agregar cookies, headers)
from fastapi import Response

# Cookie: Para leer cookies de las peticiones HTTP
from fastapi import Cookie

# Optional: Indica que un parámetro puede ser None
from typing import Optional

# --- Importaciones de modelos de datos ---
from app.models.request_models import RepositoryAnalyzeRequest, SearchRequest
from app.models.response_models import (
    RepositoryResponse,    # Respuesta con info completa de un repo
    SearchResponse,        # Respuesta con resultados de búsqueda
    SessionResponse,       # Respuesta con datos de sesión del usuario
    SearchResultItem       # Item individual de búsqueda
)

# --- Importaciones de servicios ---
# provider_detector: Detecta si una URL es de GitHub/GitLab/Azure
from app.services.provider_detector import detect_provider

# github_service: Análisis detallado de un repositorio específico
from app.services.github_service import get_github_repository

# Servicios de búsqueda para cada proveedor
from app.services.github_search_service import search_github_repositories
from app.services.gitlab_service import search_gitlab_repositories
from app.services.azure_service import search_azure_repositories

# Servicios de gestión de sesiones (cookies)
from app.services.session_service import (
    create_session,         # Crea nueva sesión (genera UUID)
    get_session,            # Obtiene datos de una sesión existente
    save_search_to_session  # Guarda búsqueda en la sesión
)

# Configuración global (tokens, nombre de cookie, etc.)
from app.core.config import settings

# Crea un router de FastAPI
# prefix="/repository": todas las rutas empezarán con /repository
# tags=["Repository"]: agrupa endpoints en la documentación de Swagger
router = APIRouter(
    prefix="/repository",
    tags=["Repository"]
)


# ============================================================================
# ENDPOINT 1: POST /repository/search - Búsqueda multi-proveedor
# ============================================================================
# @router.post: Define un endpoint que acepta peticiones POST
# response_model: FastAPI validará que la respuesta sea un SearchResponse
@router.post("/search", response_model=SearchResponse)
async def search_repositories(
    # request: Body del POST, debe tener estructura SearchRequest (campo "query")
    request: SearchRequest,

    # response: Objeto Response para modificar la respuesta HTTP
    # Lo usamos para agregar la cookie de sesión
    response: Response,

    # session_id: Lee la cookie del navegador
    # Cookie(None, alias=settings.COOKIE_NAME): Lee cookie llamada "session_id"
    # Optional[str]: Puede ser None si es la primera visita del usuario
    # FastAPI extrae automáticamente la cookie del header HTTP
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME)
):
    """
    Busca repositorios en GitHub, GitLab y Azure DevOps.
    Guarda los resultados en la sesión del usuario mediante cookies.

    Request body:
        { "query": "fastapi" }

    Response:
        {
            "query": "fastapi",
            "results": [...],
            "total_results": 10
        }

    También establece cookie "session_id" automáticamente.
    """

    # --- PASO 1: Verificar/crear sesión ---
    # Si no hay cookie O la sesión no existe en memoria
    if not session_id or not get_session(session_id):
        # Crea una nueva sesión
        # Genera un UUID único (ej: "a3f2c1b4-5678-...")
        session_id = create_session()

        # Establece la cookie en la respuesta HTTP
        # El navegador guardará esta cookie y la enviará en futuras peticiones
        response.set_cookie(
            key=settings.COOKIE_NAME,    # Nombre de la cookie: "session_id"
            value=session_id,             # Valor: UUID generado
            max_age=settings.COOKIE_MAX_AGE,  # Duración: 30 días (en segundos)

            # httponly=True: JavaScript no puede acceder a esta cookie
            # Protección contra ataques XSS (Cross-Site Scripting)
            httponly=True,

            # samesite="lax": Protección moderada contra CSRF
            # "lax": cookie se envía en navegación normal, no en POST externos
            # "strict": más seguro pero puede causar problemas de UX
            # "none": menos seguro, requiere secure=True
            samesite="lax"
        )

    # --- PASO 2: Buscar en todos los proveedores ---
    # await: Espera a que termine la función asíncrona
    # Estas 3 búsquedas se ejecutan EN PARALELO (no secuencial)
    # Python ejecuta las 3 al mismo tiempo y espera a que todas terminen
    # Tiempo total = tiempo del más lento (no suma)

    # Busca en GitHub (máximo 10 resultados, ordenados por estrellas)
    github_results = await search_github_repositories(request.query)

    # Busca en GitLab (máximo 10 resultados, ordenados por estrellas)
    gitlab_results = await search_gitlab_repositories(request.query)

    # Busca en Azure DevOps (por ahora retorna vacío)
    azure_results = await search_azure_repositories(request.query)

    # --- PASO 3: Combinar resultados ---
    # Une las 3 listas en una sola
    # Si GitHub retorna 10, GitLab retorna 5, Azure retorna 0
    # all_results tendrá 15 elementos
    all_results = github_results + gitlab_results + azure_results

    # --- PASO 4: Convertir a modelos Pydantic ---
    # Cada item es un diccionario Python
    # SearchResultItem(**item) desempaqueta el dict y crea el objeto Pydantic
    # Pydantic valida que cada item tenga todos los campos requeridos
    search_items = [SearchResultItem(**item) for item in all_results]

    # --- PASO 5: Guardar en la sesión ---
    # Guarda la búsqueda y resultados en el diccionario de sesiones
    # Esto permite recuperar los datos cuando el usuario vuelva
    save_search_to_session(session_id, request.query, all_results)

    # --- PASO 6: Retornar respuesta ---
    # FastAPI automáticamente convierte este objeto a JSON
    return SearchResponse(
        query=request.query,          # Echo de lo que se buscó
        results=search_items,         # Lista de repositorios encontrados
        total_results=len(search_items)  # Cantidad total
    )


# ============================================================================
# ENDPOINT 2: GET /repository/session - Obtener datos de sesión
# ============================================================================
@router.get("/session", response_model=SessionResponse)
async def get_session_data(
    # response: Para establecer cookie si no existe
    response: Response,

    # session_id: Lee la cookie del navegador (puede ser None)
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME)
):
    """
    Recupera los datos de la sesión del usuario.
    Si no hay sesión, crea una nueva.

    Este endpoint permite al frontend:
    1. Verificar si el usuario tiene una sesión activa
    2. Recuperar la última búsqueda realizada
    3. Recuperar los últimos resultados
    4. Ver cuántas búsquedas ha hecho

    Uso típico:
    - Al cargar la página, el frontend llama a este endpoint
    - Si hay sesión y datos guardados, los muestra automáticamente
    - Esto da la sensación de "persistencia" al reabrir el sitio
    """

    # --- Verificar si existe sesión ---
    if not session_id or not get_session(session_id):
        # No hay sesión → crear una nueva
        session_id = create_session()

        # Establecer cookie en la respuesta
        response.set_cookie(
            key=settings.COOKIE_NAME,
            value=session_id,
            max_age=settings.COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax"
        )
        # Obtener los datos de la sesión recién creada (estará vacía)
        session_data = get_session(session_id)
    else:
        # Ya existe sesión → obtener sus datos guardados
        session_data = get_session(session_id)

    # --- Retornar datos de la sesión ---
    return SessionResponse(
        session_id=session_id,  # UUID de la sesión

        # .get("key") devuelve el valor si existe, None si no existe
        last_search_query=session_data.get("last_search_query"),

        # .get("key", []) devuelve el valor si existe, [] si no existe
        last_results=session_data.get("last_results", []),

        # len() cuenta elementos de la lista "searches"
        searches_count=len(session_data.get("searches", []))
    )


# ============================================================================
# ENDPOINT 3: POST /repository/analyze - Analizar repositorio específico
# ============================================================================
@router.post("/analyze", response_model=RepositoryResponse)
async def analyze_repository(request: RepositoryAnalyzeRequest):
    """
    Analiza un repositorio específico de GitHub por URL.

    A diferencia de /search que busca MUCHOS repositorios,
    este endpoint analiza UN repositorio en detalle:
    - Commits recientes
    - Lenguajes usados
    - Estadísticas completas

    Request body:
        { "url": "https://github.com/tiangolo/fastapi" }

    Response:
        Info completa del repo (commits, lenguajes, stats, etc.)
    """

    # --- PASO 1: Detectar proveedor y extraer info ---
    # detect_provider parsea la URL y extrae owner/repo
    # Retorna tupla: (proveedor, {owner: "...", repo: "..."})
    # Ejemplo: "https://github.com/user/repo" → ("github", {"owner": "user", "repo": "repo"})
    provider, repo_info = detect_provider(str(request.url))

    # --- PASO 2: Validar que la URL sea soportada ---
    if not provider:
        # URL no reconocida o formato incorrecto
        # raise HTTPException detiene la ejecución y devuelve error HTTP
        raise HTTPException(
            status_code=400,  # Bad Request
            detail="URL no soportada. Solo se admiten repositorios de GitHub."
        )

    # --- PASO 3: Obtener información del repositorio ---
    if provider == "github":
        try:
            # Llama al servicio que obtiene info detallada de GitHub
            # Hace 3 peticiones a GitHub API:
            # 1. Info general del repo
            # 2. Lenguajes usados
            # 3. Últimos 5 commits
            data = await get_github_repository(repo_info)

            # Retorna el diccionario (FastAPI lo convierte a JSON)
            return data

        except Exception as e:
            # Si algo falla (repo no existe, token inválido, etc.)
            # Captura el error y devuelve HTTPException 500
            raise HTTPException(
                status_code=500,  # Internal Server Error
                detail=f"Error al analizar el repositorio: {str(e)}"
            )
