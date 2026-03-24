"""
repository.py - Router con todos los endpoints de la API (Producción)
"""

from fastapi import APIRouter, HTTPException, Response, Cookie
from typing import Optional

from app.models.request_models import RepositoryAnalyzeRequest, FileContentRequest, SearchRequest, MetricsRequest, CodeAnalysisRequest, CodeSuggestionsRequest, Provider
from app.models.response_models import (
    RepositoryResponse,
    RepositoryStructureResponse,
    FileContentResponse,
    SearchResponse,
    SessionResponse,
    SearchResultItem,
    MetricsResponse,
    RepositorySummary,
    AISummaryResponse,
    CodeAnalysisResponse,
    CodeSuggestionsResponse,
    FileSuggestionsResult,
    HistoryEntry,
    HistoryResponse,
)
from app.services.provider_detector import detect_provider
from app.services.github_service import get_github_repository
from app.services.github_structure_service import get_github_structure
from app.services.github_file_service import get_github_file_content, get_github_file_raw
from app.services.gitlab_analyze_service import get_gitlab_repository
from app.services.gitlab_structure_service import get_gitlab_structure
from app.services.gitlab_file_service import get_gitlab_file_content, get_gitlab_file_raw
from app.services.azure_analyze_service import get_azure_repository
from app.services.azure_structure_service import get_azure_structure
from app.services.azure_file_service import get_azure_file_content, get_azure_file_raw
from app.services.github_search_service import search_github_repositories
from app.services.gitlab_service import search_gitlab_repositories
from app.services.azure_service import search_azure_repositories
from app.services.metrics_service import calculate_metrics
from app.services.session_service import (
    create_session,
    get_session,
    save_search_to_session
)
from app.services.export_service import save_search_results
from app.services.history_service import (
    save_history_entry,
    get_history,
    get_history_entry,
    clear_history,
)
from app.services.llm_service import generate_ai_summary, analyze_code_with_ai, suggest_improvements_for_file
from app.services.report_service import generate_html_report, generate_pdf_report
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


def _ensure_session(response: Response, session_id: str | None) -> str:
    """Garantiza que exista una sesión válida. Crea una nueva si es necesario."""
    if not session_id or not get_session(session_id):
        session_id = create_session()
        _set_session_cookie(response, session_id)
    return session_id


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

    provider = filters.provider if filters else None

    github_results = await search_github_repositories(request.query, filters) if not provider or provider == Provider.GITHUB else []
    gitlab_results = await search_gitlab_repositories(request.query, filters) if not provider or provider == Provider.GITLAB else []
    azure_results = await search_azure_repositories(request.query, filters) if not provider or provider == Provider.AZURE else []

    all_results = github_results + gitlab_results + azure_results
    search_items = [SearchResultItem(**item) for item in all_results]

    filters_dict = filters.model_dump() if filters else None
    save_search_to_session(session_id, request.query, all_results, filters_dict)
    save_search_results(request.query, all_results, filters_dict)

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
async def analyze_repository(
    request: RepositoryAnalyzeRequest,
    response: Response,
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME),
):
    session_id = _ensure_session(response, session_id)
    provider, repo_info = detect_provider(str(request.url))

    if not provider:
        raise HTTPException(
            status_code=400,
            detail="URL no soportada. Solo se admiten repositorios de GitHub, GitLab y Azure DevOps."
        )

    try:
        if provider == "github":
            data = await get_github_repository(repo_info)
        elif provider == "gitlab":
            data = await get_gitlab_repository(repo_info)
        elif provider == "azure":
            data = await get_azure_repository(repo_info)

        save_history_entry(
            session_id,
            action="analyze",
            provider=data.get("provider"),
            repo_name=data.get("name"),
            repo_owner=data.get("owner"),
            url=str(request.url),
            details={
                "stars": data.get("stars", 0),
                "forks": data.get("forks", 0),
                "languages": data.get("languages", []),
                "health_score": data.get("summary", {}).get("health_score") if isinstance(data.get("summary"), dict) else None,
            },
        )
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al analizar el repositorio: {str(e)}"
        )


@router.post("/structure", response_model=RepositoryStructureResponse)
async def get_repository_structure(request: RepositoryAnalyzeRequest):
    """Obtiene la estructura de archivos y carpetas de un repositorio."""
    provider, repo_info = detect_provider(str(request.url))

    if not provider:
        raise HTTPException(
            status_code=400,
            detail="URL no soportada. Solo se admiten repositorios de GitHub, GitLab y Azure DevOps."
        )

    try:
        if provider == "github":
            data = await get_github_structure(repo_info)
            return data
        elif provider == "gitlab":
            data = await get_gitlab_structure(repo_info)
            return data
        elif provider == "azure":
            data = await get_azure_structure(repo_info)
            return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener la estructura del repositorio: {str(e)}"
        )


@router.post("/file/content", response_model=FileContentResponse)
async def get_file_content(request: FileContentRequest):
    """Obtiene el contenido de un archivo de un repositorio."""
    provider, repo_info = detect_provider(str(request.url))

    if not provider:
        raise HTTPException(
            status_code=400,
            detail="URL no soportada. Solo se admiten repositorios de GitHub, GitLab y Azure DevOps."
        )

    try:
        if provider == "github":
            data = await get_github_file_content(repo_info, request.path, request.ref)
        elif provider == "gitlab":
            data = await get_gitlab_file_content(repo_info, request.path, request.ref)
        elif provider == "azure":
            data = await get_azure_file_content(repo_info, request.path, request.ref)
        else:
            data = None

        if data is None:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")

        return data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener el contenido del archivo: {str(e)}"
        )


@router.post("/file/download")
async def download_file(request: FileContentRequest):
    """Descarga un archivo de un repositorio como bytes raw."""
    provider, repo_info = detect_provider(str(request.url))

    if not provider:
        raise HTTPException(
            status_code=400,
            detail="URL no soportada. Solo se admiten repositorios de GitHub, GitLab y Azure DevOps."
        )

    try:
        if provider == "github":
            content, file_name = await get_github_file_raw(repo_info, request.path, request.ref)
        elif provider == "gitlab":
            content, file_name = await get_gitlab_file_raw(repo_info, request.path, request.ref)
        elif provider == "azure":
            content, file_name = await get_azure_file_raw(repo_info, request.path, request.ref)
        else:
            content, file_name = None, None

        if content is None:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")

        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al descargar el archivo: {str(e)}"
        )


@router.post("/metrics", response_model=MetricsResponse)
async def get_repository_metrics(request: MetricsRequest):
    """Calcula métricas de código: complejidad ciclomática, líneas por función, ratio comentario/código."""
    provider, repo_info = detect_provider(str(request.url))

    if not provider:
        raise HTTPException(
            status_code=400,
            detail="URL no soportada. Solo se admiten repositorios de GitHub, GitLab y Azure DevOps."
        )

    try:
        data = await calculate_metrics(provider, repo_info, request.max_files)
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al calcular métricas del repositorio: {str(e)}"
        )


@router.post("/ai/summary", response_model=AISummaryResponse)
async def ai_repository_summary(
    request: RepositoryAnalyzeRequest,
    response: Response,
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME),
):
    """Genera un resumen inteligente del repositorio usando Claude."""
    session_id = _ensure_session(response, session_id)
    provider, repo_info = detect_provider(str(request.url))

    if not provider:
        raise HTTPException(
            status_code=400,
            detail="URL no soportada. Solo se admiten repositorios de GitHub, GitLab y Azure DevOps."
        )

    try:
        if provider == "github":
            repo_data = await get_github_repository(repo_info)
        elif provider == "gitlab":
            repo_data = await get_gitlab_repository(repo_info)
        elif provider == "azure":
            repo_data = await get_azure_repository(repo_info)

        ai_summary = await generate_ai_summary(repo_data)

        save_history_entry(
            session_id,
            action="ai_summary",
            provider=repo_data["provider"],
            repo_name=repo_data["name"],
            repo_owner=repo_data["owner"],
            url=str(request.url),
            details={"summary_preview": ai_summary[:200]},
        )

        return AISummaryResponse(
            provider=repo_data["provider"],
            owner=repo_data["owner"],
            name=repo_data["name"],
            ai_summary=ai_summary,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar resumen con IA: {str(e)}"
        )


@router.post("/ai/code-analysis", response_model=CodeAnalysisResponse)
async def ai_code_analysis(
    request: CodeAnalysisRequest,
    response: Response,
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME),
):
    """Analiza la calidad de un archivo de código usando Claude."""
    session_id = _ensure_session(response, session_id)
    provider, repo_info = detect_provider(str(request.url))

    if not provider:
        raise HTTPException(
            status_code=400,
            detail="URL no soportada. Solo se admiten repositorios de GitHub, GitLab y Azure DevOps."
        )

    try:
        if provider == "github":
            file_data = await get_github_file_content(repo_info, request.path, request.ref)
        elif provider == "gitlab":
            file_data = await get_gitlab_file_content(repo_info, request.path, request.ref)
        elif provider == "azure":
            file_data = await get_azure_file_content(repo_info, request.path, request.ref)
        else:
            file_data = None

        if file_data is None:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")

        if file_data.get("is_binary", False):
            raise HTTPException(status_code=400, detail="No se puede analizar archivos binarios")

        language = request.path.rsplit(".", 1)[-1] if "." in request.path else "text"
        analysis = await analyze_code_with_ai(request.path, file_data["content"], language)

        save_history_entry(
            session_id,
            action="ai_code_analysis",
            provider=provider,
            repo_name=repo_info.get("repo"),
            repo_owner=repo_info.get("owner"),
            url=str(request.url),
            details={
                "file_path": request.path,
                "language": language,
                "quality_score": analysis.get("quality_score", 0),
            },
        )

        return CodeAnalysisResponse(
            file_path=request.path,
            language=language,
            quality_score=analysis.get("quality_score", 0),
            summary=analysis.get("summary", ""),
            strengths=analysis.get("strengths", []),
            improvements=analysis.get("improvements", []),
            patterns=analysis.get("patterns", []),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al analizar código con IA: {str(e)}"
        )


@router.post("/ai/suggestions", response_model=CodeSuggestionsResponse)
async def ai_code_suggestions(
    request: CodeSuggestionsRequest,
    response: Response,
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME),
):
    """Recibe uno o varios archivos, devuelve sugerencias por archivo con líneas, snippets y diff."""
    session_id = _ensure_session(response, session_id)

    for f in request.files:
        if not f.code.strip():
            raise HTTPException(
                status_code=400,
                detail=f"El archivo '{f.file_name}' no puede tener código vacío"
            )

    try:
        import asyncio
        tasks = [
            suggest_improvements_for_file(f.code, f.language, f.file_name)
            for f in request.files
        ]
        results = await asyncio.gather(*tasks)

        file_results = []
        total = 0
        for r in results:
            suggestions = r.get("suggestions", [])
            total += len(suggestions)
            file_results.append(FileSuggestionsResult(
                file_name=r["file_name"],
                language=r["language"],
                suggestions=suggestions,
                improved_code=r.get("improved_code", ""),
                diff=r.get("diff", ""),
            ))

        save_history_entry(
            session_id,
            action="ai_suggestions",
            details={
                "files_count": len(request.files),
                "file_names": [f.file_name for f in request.files],
                "total_suggestions": total,
            },
        )

        return CodeSuggestionsResponse(
            total_suggestions=total,
            files=file_results,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar sugerencias con IA: {str(e)}"
        )


@router.post("/ai/suggestions/report")
async def ai_suggestions_report(request: CodeSuggestionsRequest):
    """Genera un reporte HTML autocontenido con las sugerencias de mejora por archivo."""
    for f in request.files:
        if not f.code.strip():
            raise HTTPException(
                status_code=400,
                detail=f"El archivo '{f.file_name}' no puede tener codigo vacio"
            )

    try:
        import asyncio
        tasks = [
            suggest_improvements_for_file(f.code, f.language, f.file_name)
            for f in request.files
        ]
        results = await asyncio.gather(*tasks)

        file_results = []
        total = 0
        for r in results:
            suggestions = r.get("suggestions", [])
            total += len(suggestions)
            file_results.append({
                "file_name": r["file_name"],
                "language": r["language"],
                "suggestions": suggestions,
                "improved_code": r.get("improved_code", ""),
                "diff": r.get("diff", ""),
            })

        html = generate_html_report({
            "total_suggestions": total,
            "files": file_results,
        })

        return Response(
            content=html,
            media_type="text/html",
            headers={"Content-Disposition": 'inline; filename="gitzy-report.html"'},
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar reporte: {str(e)}"
        )


@router.post("/ai/suggestions/report/pdf")
async def ai_suggestions_report_pdf(request: CodeSuggestionsRequest):
    """Genera un reporte PDF con las sugerencias de mejora por archivo."""
    for f in request.files:
        if not f.code.strip():
            raise HTTPException(
                status_code=400,
                detail=f"El archivo '{f.file_name}' no puede tener codigo vacio"
            )

    try:
        import asyncio
        tasks = [
            suggest_improvements_for_file(f.code, f.language, f.file_name)
            for f in request.files
        ]
        results = await asyncio.gather(*tasks)

        file_results = []
        total = 0
        for r in results:
            suggestions = r.get("suggestions", [])
            total += len(suggestions)
            file_results.append({
                "file_name": r["file_name"],
                "language": r["language"],
                "suggestions": suggestions,
                "improved_code": r.get("improved_code", ""),
                "diff": r.get("diff", ""),
            })

        pdf_bytes = generate_pdf_report({
            "total_suggestions": total,
            "files": file_results,
        })

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="gitzy-report.pdf"'},
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar reporte PDF: {str(e)}"
        )


# ---------------------------------------------------------------------------
# History endpoints
# ---------------------------------------------------------------------------

@router.get("/history", response_model=HistoryResponse)
async def get_analysis_history(
    response: Response,
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME),
):
    """Devuelve el historial de análisis previos de la sesión actual."""
    session_id = _ensure_session(response, session_id)
    entries = get_history(session_id)

    return HistoryResponse(
        session_id=session_id,
        total_entries=len(entries),
        entries=entries,
    )


@router.get("/history/{entry_id}", response_model=HistoryEntry)
async def get_analysis_history_entry(
    entry_id: str,
    response: Response,
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME),
):
    """Devuelve una entrada específica del historial."""
    session_id = _ensure_session(response, session_id)
    entry = get_history_entry(session_id, entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada en el historial")

    return entry


@router.delete("/history")
async def delete_analysis_history(
    response: Response,
    session_id: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME),
):
    """Limpia todo el historial de análisis de la sesión actual."""
    session_id = _ensure_session(response, session_id)
    deleted = clear_history(session_id)

    return {"message": f"Historial limpiado: {deleted} entradas eliminadas"}
