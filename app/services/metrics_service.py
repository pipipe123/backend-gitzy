"""
metrics_service.py - Orquestación del cálculo de métricas de código

Obtiene archivos del repositorio y calcula métricas usando python_analyzer.
"""

import asyncio
import re
from urllib.parse import quote

from app.core.config import settings
from app.utils.http_client import get
from app.utils.python_analyzer import analyze_python_source
from app.services.github_file_service import get_github_file_content
from app.services.gitlab_file_service import get_gitlab_file_content
from app.services.azure_file_service import get_azure_file_content


# Patrones de archivos a excluir del análisis
_EXCLUDE_PATTERNS = re.compile(
    r"(^|/)(test_|tests/|test/|migrations/|__pycache__/|\.tox/|\.venv/|venv/|env/)"
)
_EXCLUDE_SUFFIXES = ("_test.py", "__init__.py", "conftest.py", "setup.py")

# Límite de concurrencia para llamadas a la API
_SEMAPHORE_LIMIT = 10

# Tamaño máximo de archivo a analizar (100KB)
_MAX_FILE_SIZE = 100_000


async def _get_flat_file_list_github(repo_info: dict) -> list[str]:
    """Obtiene lista plana de paths de archivos .py desde GitHub."""
    owner = repo_info["owner"]
    repo = repo_info["repo"]
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # Obtener rama por defecto
    repo_response = await get(f"https://api.github.com/repos/{owner}/{repo}", headers)
    if repo_response.status_code != 200:
        raise Exception(f"Error obteniendo repositorio: {repo_response.status_code}")
    default_branch = repo_response.json()["default_branch"]

    # Obtener árbol recursivo
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
    tree_response = await get(tree_url, headers)
    if tree_response.status_code != 200:
        raise Exception(f"Error obteniendo árbol: {tree_response.status_code}")

    items = tree_response.json().get("tree", [])
    return [item["path"] for item in items if item.get("type") == "blob"]


async def _get_flat_file_list_gitlab(repo_info: dict) -> list[str]:
    """Obtiene lista plana de paths de archivos .py desde GitLab."""
    owner = repo_info["owner"]
    repo = repo_info["repo"]
    headers = {}
    if settings.GITLAB_TOKEN:
        headers["PRIVATE-TOKEN"] = settings.GITLAB_TOKEN

    project_path = quote(f"{owner}/{repo}", safe="")

    # Obtener rama por defecto
    project_url = f"https://gitlab.com/api/v4/projects/{project_path}"
    project_response = await get(project_url, headers if headers else None)
    if project_response.status_code != 200:
        raise Exception(f"Error obteniendo proyecto: {project_response.status_code}")
    default_branch = project_response.json().get("default_branch", "main")

    # Obtener árbol recursivo con paginación
    all_paths = []
    page = 1
    per_page = 100

    while True:
        tree_url = (
            f"https://gitlab.com/api/v4/projects/{project_path}"
            f"/repository/tree?recursive=true&per_page={per_page}&page={page}"
            f"&ref={default_branch}"
        )
        tree_response = await get(tree_url, headers if headers else None)
        if tree_response.status_code != 200:
            raise Exception(f"Error obteniendo árbol: {tree_response.status_code}")

        items = tree_response.json()
        if not items:
            break

        for item in items:
            if item.get("type") == "blob":
                all_paths.append(item["path"])

        page += 1
        if page > 50:
            break

    return all_paths


async def _get_flat_file_list_azure(repo_info: dict) -> list[str]:
    """Obtiene lista plana de paths de archivos .py desde Azure DevOps."""
    import base64 as b64
    org = repo_info.get("organization", settings.AZURE_ORGANIZATION)
    project = repo_info["project"]
    repo = repo_info["repo"]

    credentials = b64.b64encode(f":{settings.AZURE_TOKEN}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }

    base_url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}"

    # Obtener rama por defecto
    repo_response = await get(f"{base_url}?api-version=7.0", headers)
    if repo_response.status_code != 200:
        raise Exception(f"Error obteniendo repositorio: {repo_response.status_code}")

    repo_data = repo_response.json()
    default_branch = repo_data.get("defaultBranch", "refs/heads/main")
    if default_branch.startswith("refs/heads/"):
        default_branch = default_branch[len("refs/heads/"):]

    items_url = (
        f"{base_url}/items?recursionLevel=Full"
        f"&versionDescriptor.version={default_branch}"
        f"&api-version=7.0"
    )
    items_response = await get(items_url, headers)
    if items_response.status_code != 200:
        raise Exception(f"Error obteniendo estructura: {items_response.status_code}")

    items = items_response.json().get("value", [])
    paths = []
    for item in items:
        if item.get("isFolder", False):
            continue
        path = item.get("path", "")
        if path.startswith("/"):
            path = path[1:]
        if path:
            paths.append(path)

    return paths


def _filter_python_files(paths: list[str], max_files: int) -> list[str]:
    """Filtra a archivos .py relevantes, ordenados por profundidad."""
    python_files = []
    for path in paths:
        if not path.endswith(".py"):
            continue
        if _EXCLUDE_PATTERNS.search(path):
            continue
        if path.endswith(_EXCLUDE_SUFFIXES):
            continue
        python_files.append(path)

    # Ordenar por profundidad (menos profundos primero)
    python_files.sort(key=lambda p: p.count("/"))
    return python_files[:max_files]


async def _fetch_file_content(
    provider: str,
    repo_info: dict,
    path: str,
    semaphore: asyncio.Semaphore,
) -> tuple[str, str | None]:
    """Obtiene contenido de un archivo. Retorna (path, content) o (path, None) si falla."""
    async with semaphore:
        try:
            if provider == "github":
                data = await get_github_file_content(repo_info, path)
            elif provider == "gitlab":
                data = await get_gitlab_file_content(repo_info, path)
            elif provider == "azure":
                data = await get_azure_file_content(repo_info, path)
            else:
                return path, None

            if data is None or data.get("is_binary", False):
                return path, None

            content = data.get("content", "")
            if len(content) > _MAX_FILE_SIZE:
                return path, None

            return path, content
        except Exception:
            return path, None


async def calculate_metrics(provider: str, repo_info: dict, max_files: int = 30) -> dict:
    """
    Calcula métricas de código para un repositorio.

    Retorna dict compatible con MetricsResponse.
    """
    # 1. Obtener lista plana de archivos
    if provider == "github":
        all_paths = await _get_flat_file_list_github(repo_info)
        owner = repo_info["owner"]
        name = repo_info["repo"]
    elif provider == "gitlab":
        all_paths = await _get_flat_file_list_gitlab(repo_info)
        owner = repo_info["owner"]
        name = repo_info["repo"]
    elif provider == "azure":
        all_paths = await _get_flat_file_list_azure(repo_info)
        owner = repo_info.get("project", "")
        name = repo_info["repo"]
    else:
        raise Exception(f"Proveedor no soportado: {provider}")

    # 2. Filtrar a archivos Python
    python_files = _filter_python_files(all_paths, max_files)

    if not python_files:
        return _empty_response(provider, owner, name)

    # 3. Descargar archivos en paralelo
    semaphore = asyncio.Semaphore(_SEMAPHORE_LIMIT)
    tasks = [
        _fetch_file_content(provider, repo_info, path, semaphore)
        for path in python_files
    ]
    results = await asyncio.gather(*tasks)

    # 4. Analizar cada archivo
    files_metrics = []
    files_skipped = 0

    for path, content in results:
        if content is None:
            files_skipped += 1
            continue

        analysis = analyze_python_source(content)
        if analysis is None:
            files_skipped += 1
            continue

        files_metrics.append({
            "path": path,
            **analysis,
        })

    if not files_metrics:
        return _empty_response(provider, owner, name, files_skipped=files_skipped)

    # 5. Calcular resumen agregado
    all_functions = []
    total_code_lines = 0
    total_comment_lines = 0

    for fm in files_metrics:
        all_functions.extend(fm["functions"])
        total_code_lines += fm["code_lines"]
        total_comment_lines += fm["comment_lines"]

    total_functions = len(all_functions)
    avg_complexity = (
        sum(f["cyclomatic_complexity"] for f in all_functions) / total_functions
        if total_functions > 0 else 0.0
    )
    avg_lines = (
        sum(f["lines"] for f in all_functions) / total_functions
        if total_functions > 0 else 0.0
    )
    global_ratio = (
        total_comment_lines / total_code_lines
        if total_code_lines > 0 else 0.0
    )

    return {
        "provider": provider,
        "owner": owner,
        "name": name,
        "language": "Python",
        "files_analyzed": len(files_metrics),
        "files_skipped": files_skipped,
        "summary": {
            "avg_cyclomatic_complexity": round(avg_complexity, 2),
            "avg_lines_per_function": round(avg_lines, 2),
            "comment_code_ratio": round(global_ratio, 4),
            "total_functions": total_functions,
            "total_lines_of_code": total_code_lines,
            "total_comment_lines": total_comment_lines,
        },
        "files": files_metrics,
    }


def _empty_response(provider: str, owner: str, name: str, files_skipped: int = 0) -> dict:
    """Respuesta vacía cuando no hay archivos Python para analizar."""
    return {
        "provider": provider,
        "owner": owner,
        "name": name,
        "language": "Python",
        "files_analyzed": 0,
        "files_skipped": files_skipped,
        "summary": {
            "avg_cyclomatic_complexity": 0.0,
            "avg_lines_per_function": 0.0,
            "comment_code_ratio": 0.0,
            "total_functions": 0,
            "total_lines_of_code": 0,
            "total_comment_lines": 0,
        },
        "files": [],
    }
