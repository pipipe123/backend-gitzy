"""
gitlab_file_service.py - Lectura y descarga de archivos de repositorios GitLab

API Endpoints:
- GET /api/v4/projects/{id}/repository/files/{file_path}?ref={branch} → JSON con base64
- GET /api/v4/projects/{id}/repository/files/{file_path}/raw?ref={branch} → bytes raw
"""

import base64
from urllib.parse import quote

from app.core.config import settings
from app.utils.http_client import get


def _get_headers() -> dict:
    headers = {}
    if settings.GITLAB_TOKEN:
        headers["PRIVATE-TOKEN"] = settings.GITLAB_TOKEN
    return headers


async def _get_default_branch(project_path: str, headers: dict) -> str:
    """Obtiene la rama por defecto del proyecto."""
    url = f"https://gitlab.com/api/v4/projects/{project_path}"
    response = await get(url, headers if headers else None)
    if response.status_code != 200:
        raise Exception(f"Error obteniendo proyecto de GitLab: {response.status_code}")
    return response.json().get("default_branch", "main")


async def get_gitlab_file_content(repo_info: dict, path: str, ref: str = None) -> dict:
    """Obtiene el contenido de un archivo como texto (o base64 si es binario)."""
    owner = repo_info["owner"]
    repo = repo_info["repo"]
    headers = _get_headers()

    project_path = quote(f"{owner}/{repo}", safe="")

    if not ref:
        ref = await _get_default_branch(project_path, headers)

    # GitLab requiere que el file_path esté URL-encoded
    encoded_file_path = quote(path, safe="")
    url = (
        f"https://gitlab.com/api/v4/projects/{project_path}"
        f"/repository/files/{encoded_file_path}?ref={ref}"
    )

    response = await get(url, headers if headers else None)

    if response.status_code == 404:
        return None

    if response.status_code != 200:
        raise Exception(f"Error obteniendo archivo de GitLab: {response.status_code}")

    data = response.json()

    file_content = data.get("content", "")
    encoding = data.get("encoding", "base64")
    size = data.get("size", 0)
    file_name = data.get("file_name", path.split("/")[-1])

    is_binary = False
    if encoding == "base64" and file_content:
        try:
            decoded = base64.b64decode(file_content).decode("utf-8")
            content = decoded
            encoding = "utf-8"
        except UnicodeDecodeError:
            content = file_content
            encoding = "base64"
            is_binary = True
    else:
        content = file_content
        encoding = encoding or "utf-8"

    return {
        "provider": "gitlab",
        "repo_name": repo,
        "file_path": path,
        "file_name": file_name,
        "content": content,
        "encoding": encoding,
        "size": size,
        "is_binary": is_binary,
    }


async def get_gitlab_file_raw(repo_info: dict, path: str, ref: str = None) -> tuple:
    """Obtiene el contenido raw (bytes) de un archivo para descarga."""
    owner = repo_info["owner"]
    repo = repo_info["repo"]
    headers = _get_headers()

    project_path = quote(f"{owner}/{repo}", safe="")

    if not ref:
        ref = await _get_default_branch(project_path, headers)

    encoded_file_path = quote(path, safe="")
    url = (
        f"https://gitlab.com/api/v4/projects/{project_path}"
        f"/repository/files/{encoded_file_path}/raw?ref={ref}"
    )

    response = await get(url, headers if headers else None)

    if response.status_code == 404:
        return None, None

    if response.status_code != 200:
        raise Exception(f"Error descargando archivo de GitLab: {response.status_code}")

    file_name = path.split("/")[-1]
    return response.content, file_name
