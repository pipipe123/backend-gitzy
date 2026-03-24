"""
azure_analyze_service.py - Análisis detallado de un repositorio en Azure DevOps

Obtiene información completa de un repositorio Git en Azure DevOps:
- Datos generales (nombre, rama por defecto, tamaño, etc.)
- Últimos 5 commits

API Endpoints:
- GET https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}?api-version=7.0
- GET https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}/commits?$top=5&api-version=7.0

Nota: Azure DevOps no tiene endpoint de lenguajes como GitHub/GitLab.
"""

import base64

from app.core.config import settings
from app.utils.http_client import get
from app.services.summary_service import generate_repository_summary


def _get_azure_headers() -> dict:
    credentials = base64.b64encode(f":{settings.AZURE_TOKEN}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }


async def get_azure_repository(repo_info: dict) -> dict:
    org = repo_info.get("organization", settings.AZURE_ORGANIZATION)
    project = repo_info["project"]
    repo = repo_info["repo"]

    headers = _get_azure_headers()
    base_url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}"

    # Información general del repositorio
    repo_response = await get(f"{base_url}?api-version=7.0", headers)
    if repo_response.status_code != 200:
        raise Exception(f"Error obteniendo repositorio de Azure DevOps: {repo_response.status_code}")

    repo_data = repo_response.json()

    # Últimos 5 commits
    commits_response = await get(f"{base_url}/commits?$top=5&api-version=7.0", headers)
    commits = []
    if commits_response.status_code == 200:
        for commit in commits_response.json().get("value", []):
            commits.append({
                "sha": commit.get("commitId", ""),
                "message": commit.get("comment", ""),
                "author": commit.get("author", {}).get("name")
            })

    project_data = repo_data.get("project", {})
    default_branch = repo_data.get("defaultBranch", "refs/heads/main")
    # Azure devuelve "refs/heads/main", extraemos solo "main"
    if default_branch.startswith("refs/heads/"):
        default_branch = default_branch[len("refs/heads/"):]

    web_url = repo_data.get("webUrl", "")

    result = {
        "provider": "azure",
        "name": repo_data.get("name", ""),
        "owner": project_data.get("name", org),
        "description": project_data.get("description"),
        "is_private": True,  # Azure DevOps repos son privados por defecto
        "default_branch": default_branch,
        "created_at": project_data.get("lastUpdateTime", ""),
        "updated_at": project_data.get("lastUpdateTime", ""),
        "stars": 0,  # Azure DevOps no tiene estrellas
        "forks": 0,  # Azure DevOps no tiene forks públicos
        "open_issues": 0,  # Requeriría llamar a la API de Work Items
        "languages": [],  # Azure no tiene endpoint de lenguajes
        "commits": commits,
        "url": web_url
    }

    result["summary"] = generate_repository_summary(result)

    return result
