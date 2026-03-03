"""
azure_structure_service.py - Estructura de archivos de un repositorio en Azure DevOps

Obtiene el árbol completo de archivos y carpetas de un repositorio Git.

API Endpoint:
- GET https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}/items?recursionLevel=Full&api-version=7.0
"""

import base64

from app.core.config import settings
from app.utils.http_client import get
from app.utils.tree_builder import build_nested_tree


def _get_azure_headers() -> dict:
    credentials = base64.b64encode(f":{settings.AZURE_TOKEN}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }


async def get_azure_structure(repo_info: dict) -> dict:
    org = repo_info.get("organization", settings.AZURE_ORGANIZATION)
    project = repo_info["project"]
    repo = repo_info["repo"]

    headers = _get_azure_headers()
    base_url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}"

    # Obtener info del repo para la rama por defecto
    repo_response = await get(f"{base_url}?api-version=7.0", headers)
    if repo_response.status_code != 200:
        raise Exception(f"Error obteniendo repositorio de Azure DevOps: {repo_response.status_code}")

    repo_data = repo_response.json()
    default_branch = repo_data.get("defaultBranch", "refs/heads/main")
    if default_branch.startswith("refs/heads/"):
        default_branch = default_branch[len("refs/heads/"):]

    # Obtener árbol de archivos recursivo
    items_url = (
        f"{base_url}/items?recursionLevel=Full"
        f"&versionDescriptor.version={default_branch}"
        f"&api-version=7.0"
    )
    items_response = await get(items_url, headers)
    if items_response.status_code != 200:
        raise Exception(f"Error obteniendo estructura de Azure DevOps: {items_response.status_code}")

    items = items_response.json().get("value", [])

    # Normalizar al formato que espera build_nested_tree
    # Azure usa "isFolder" (bool) y "path" empieza con "/"
    normalized_items = []
    for item in items:
        path = item.get("path", "")
        # Azure devuelve paths con "/" al inicio, lo quitamos
        if path.startswith("/"):
            path = path[1:]
        # Ignorar el root vacío
        if not path:
            continue

        is_folder = item.get("isFolder", False)
        normalized_items.append({
            "path": path,
            "type": "tree" if is_folder else "blob",
            "size": item.get("contentMetadata", {}).get("contentLength") if not is_folder else None
        })

    nested_tree, file_count, dir_count = build_nested_tree(normalized_items)

    return {
        "provider": "azure",
        "owner": project,
        "name": repo,
        "default_branch": default_branch,
        "total_files": file_count,
        "total_directories": dir_count,
        "tree": nested_tree
    }
