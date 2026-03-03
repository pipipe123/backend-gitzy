"""
gitlab_analyze_service.py - Análisis detallado de un repositorio en GitLab

Obtiene información completa de un proyecto GitLab:
- Datos generales (nombre, descripción, estrellas, forks, etc.)
- Lenguajes utilizados
- Últimos 5 commits

API Endpoints:
- GET https://gitlab.com/api/v4/projects/{id}
- GET https://gitlab.com/api/v4/projects/{id}/languages
- GET https://gitlab.com/api/v4/projects/{id}/repository/commits
"""

from urllib.parse import quote

from app.core.config import settings
from app.utils.http_client import get


async def get_gitlab_repository(repo_info: dict) -> dict:
    owner = repo_info["owner"]
    repo = repo_info["repo"]

    headers = {}
    if settings.GITLAB_TOKEN:
        headers["PRIVATE-TOKEN"] = settings.GITLAB_TOKEN

    project_path = quote(f"{owner}/{repo}", safe="")
    base_url = f"https://gitlab.com/api/v4/projects/{project_path}"

    # Información general del proyecto
    project_response = await get(base_url, headers if headers else None)
    if project_response.status_code != 200:
        raise Exception(f"Error obteniendo proyecto de GitLab: {project_response.status_code}")

    project_data = project_response.json()

    # Lenguajes
    languages_response = await get(f"{base_url}/languages", headers if headers else None)
    languages = list(languages_response.json().keys()) if languages_response.status_code == 200 else []

    # Últimos 5 commits
    commits_response = await get(f"{base_url}/repository/commits?per_page=5", headers if headers else None)
    commits = []
    if commits_response.status_code == 200:
        for commit in commits_response.json():
            commits.append({
                "sha": commit.get("id", ""),
                "message": commit.get("message", ""),
                "author": commit.get("author_name")
            })

    return {
        "provider": "gitlab",
        "name": project_data.get("name", ""),
        "owner": project_data.get("namespace", {}).get("name", ""),
        "description": project_data.get("description"),
        "is_private": project_data.get("visibility", "public") != "public",
        "default_branch": project_data.get("default_branch", "main"),
        "created_at": project_data.get("created_at", ""),
        "updated_at": project_data.get("last_activity_at", ""),
        "stars": project_data.get("star_count", 0),
        "forks": project_data.get("forks_count", 0),
        "open_issues": project_data.get("open_issues_count", 0),
        "languages": languages,
        "commits": commits,
        "url": project_data.get("web_url", "")
    }
