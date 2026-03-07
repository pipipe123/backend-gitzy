"""
github_file_service.py - Lectura y descarga de archivos de repositorios GitHub

API Endpoints:
- GET /repos/{owner}/{repo}/contents/{path}?ref={branch} → JSON con contenido base64
- Mismo endpoint con Accept: application/vnd.github.raw → bytes raw
"""

import base64

from app.core.config import settings
from app.utils.http_client import get


def _get_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }


async def _get_default_branch(owner: str, repo: str, headers: dict) -> str:
    """Obtiene la rama por defecto del repositorio."""
    response = await get(f"https://api.github.com/repos/{owner}/{repo}", headers)
    if response.status_code != 200:
        raise Exception(f"Error obteniendo info del repositorio: {response.status_code}")
    return response.json()["default_branch"]


async def get_github_file_content(repo_info: dict, path: str, ref: str = None) -> dict:
    """Obtiene el contenido de un archivo como texto (o base64 si es binario)."""
    owner = repo_info["owner"]
    repo = repo_info["repo"]
    headers = _get_headers()

    if not ref:
        ref = await _get_default_branch(owner, repo, headers)

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    response = await get(url, headers)

    if response.status_code == 404:
        return None

    if response.status_code != 200:
        raise Exception(f"Error obteniendo archivo: {response.status_code}")

    data = response.json()

    # Verificar que es un archivo, no un directorio
    if isinstance(data, list):
        raise Exception("La ruta especificada es un directorio, no un archivo")

    file_content = data.get("content", "")
    encoding = data.get("encoding", "")
    size = data.get("size", 0)
    file_name = data.get("name", path.split("/")[-1])

    is_binary = False
    if encoding == "base64" and file_content:
        try:
            decoded = base64.b64decode(file_content).decode("utf-8")
            content = decoded
            encoding = "utf-8"
        except UnicodeDecodeError:
            content = file_content.replace("\n", "")
            encoding = "base64"
            is_binary = True
    else:
        content = file_content
        encoding = encoding or "utf-8"

    return {
        "provider": "github",
        "repo_name": repo,
        "file_path": path,
        "file_name": file_name,
        "content": content,
        "encoding": encoding,
        "size": size,
        "is_binary": is_binary,
    }


async def get_github_file_raw(repo_info: dict, path: str, ref: str = None) -> tuple:
    """Obtiene el contenido raw (bytes) de un archivo para descarga."""
    owner = repo_info["owner"]
    repo = repo_info["repo"]
    headers = _get_headers()

    if not ref:
        ref = await _get_default_branch(owner, repo, headers)

    # Usar header raw para obtener bytes directamente
    raw_headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.raw+json"
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    response = await get(url, raw_headers)

    if response.status_code == 404:
        return None, None

    if response.status_code != 200:
        raise Exception(f"Error descargando archivo: {response.status_code}")

    file_name = path.split("/")[-1]
    return response.content, file_name
