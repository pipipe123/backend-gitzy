"""
azure_file_service.py - Lectura y descarga de archivos de repositorios Azure DevOps

API Endpoints:
- GET /{org}/{project}/_apis/git/repositories/{repo}/items?path={path}&api-version=7.0
  - Con &includeContent=true&$format=json → JSON con contenido
  - Sin esos params → bytes raw
"""

import base64

from app.core.config import settings
from app.utils.http_client import get


def _get_headers() -> dict:
    credentials = base64.b64encode(f":{settings.AZURE_TOKEN}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }


async def _get_default_branch(base_url: str, headers: dict) -> str:
    """Obtiene la rama por defecto del repositorio."""
    response = await get(f"{base_url}?api-version=7.0", headers)
    if response.status_code != 200:
        raise Exception(f"Error obteniendo repositorio de Azure DevOps: {response.status_code}")
    default_branch = response.json().get("defaultBranch", "refs/heads/main")
    if default_branch.startswith("refs/heads/"):
        default_branch = default_branch[len("refs/heads/"):]
    return default_branch


async def get_azure_file_content(repo_info: dict, path: str, ref: str = None) -> dict:
    """Obtiene el contenido de un archivo como texto (o base64 si es binario)."""
    org = repo_info.get("organization", settings.AZURE_ORGANIZATION)
    project = repo_info["project"]
    repo = repo_info["repo"]
    headers = _get_headers()

    base_url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}"

    if not ref:
        ref = await _get_default_branch(base_url, headers)

    url = (
        f"{base_url}/items?path={path}"
        f"&includeContent=true&$format=json"
        f"&versionDescriptor.version={ref}"
        f"&api-version=7.0"
    )

    response = await get(url, headers)

    if response.status_code == 404:
        return None

    if response.status_code != 200:
        raise Exception(f"Error obteniendo archivo de Azure DevOps: {response.status_code}")

    data = response.json()
    content_raw = data.get("content", "")
    is_binary = data.get("isBinary", False)
    file_name = path.split("/")[-1]

    if is_binary:
        encoding = "base64"
        content = base64.b64encode(content_raw.encode("latin-1")).decode("ascii") if content_raw else ""
    else:
        encoding = "utf-8"
        content = content_raw

    return {
        "provider": "azure",
        "repo_name": repo,
        "file_path": path,
        "file_name": file_name,
        "content": content,
        "encoding": encoding,
        "size": len(content_raw) if content_raw else 0,
        "is_binary": is_binary,
    }


async def get_azure_file_raw(repo_info: dict, path: str, ref: str = None) -> tuple:
    """Obtiene el contenido raw (bytes) de un archivo para descarga."""
    org = repo_info.get("organization", settings.AZURE_ORGANIZATION)
    project = repo_info["project"]
    repo = repo_info["repo"]
    headers = _get_headers()

    base_url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}"

    if not ref:
        ref = await _get_default_branch(base_url, headers)

    url = (
        f"{base_url}/items?path={path}"
        f"&versionDescriptor.version={ref}"
        f"&api-version=7.0"
    )

    response = await get(url, headers)

    if response.status_code == 404:
        return None, None

    if response.status_code != 200:
        raise Exception(f"Error descargando archivo de Azure DevOps: {response.status_code}")

    file_name = path.split("/")[-1]
    return response.content, file_name
