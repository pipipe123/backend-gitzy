"""
repository.py - Router con todos los endpoints de la API (Producción)
"""

from fastapi import APIRouter, HTTPException, Response, Cookie
from typing import Optional

from app.models.request_models import RepositoryAnalyzeRequest, SearchRequest
from app.models.response_models import (
    RepositoryResponse,
    SearchResponse,
    SessionResponse,
    SearchResultItem
)
from app.services.provider_detector import detect_provider
from app.services.github_service import get_github_repository
from app.services.github_search_service import search_github_repositories
from app.services.gitlab_service import search_gitlab_repositories
from app.services.azure_service import search_azure_repositories
from app.services.session_service import (
    create_session,
    get_session,
    save_search_to_session
)
from app.core.config import settings

router = APIRouter(
    prefix="/repository",
    tags=["Repository"]
)


def _set_session_cookie(response: Response, session_id: str):
    """Establece la cookie de sesión con configuración segura para producción."""
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=session_id,
        max_age=settings.COOKIE_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="none",
    )


@router.post("/search", response_model=SearchResponse)
async def search_repositories(
    request: SearchRequest,
    response: Response,
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME)
):
    if not session_id or not get_session(session_id):
        session_id = create_session()
        _set_session_cookie(response, session_id)

    filters = request.filters

    github_results = await search_github_repositories(request.query, filters)
    gitlab_results = await search_gitlab_repositories(request.query, filters)
    azure_results = await search_azure_repositories(request.query, filters)

    all_results = github_results + gitlab_results + azure_results
    search_items = [SearchResultItem(**item) for item in all_results]

    filters_dict = filters.model_dump() if filters else None
    save_search_to_session(session_id, request.query, all_results, filters_dict)

    return SearchResponse(
        query=request.query,
        filters=filters_dict,
        results=search_items,
        total_results=len(search_items)
    )


@router.get("/session", response_model=SessionResponse)
async def get_session_data(
    response: Response,
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME)
):
    if not session_id or not get_session(session_id):
        session_id = create_session()
        _set_session_cookie(response, session_id)
        session_data = get_session(session_id)
    else:
        session_data = get_session(session_id)

    return SessionResponse(
        session_id=session_id,
        last_search_query=session_data.get("last_search_query"),
        last_search_filters=session_data.get("last_search_filters"),
        last_results=session_data.get("last_results", []),
        searches_count=len(session_data.get("searches", []))
    )


@router.post("/analyze", response_model=RepositoryResponse)
async def analyze_repository(request: RepositoryAnalyzeRequest):
    provider, repo_info = detect_provider(str(request.url))

    if not provider:
        raise HTTPException(
            status_code=400,
            detail="URL no soportada. Solo se admiten repositorios de GitHub."
        )

    if provider == "github":
        try:
            data = await get_github_repository(repo_info)
            return data
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al analizar el repositorio: {str(e)}"
            )
