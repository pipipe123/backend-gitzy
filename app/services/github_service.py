from app.core.config import settings
from app.utils.http_client import get


async def get_github_repository(repo_info: dict):
    owner = repo_info["owner"]
    repo = repo_info["repo"]

    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    # Información general
    repo_response = await get(base_url, headers)
    if repo_response.status_code != 200:
        raise Exception("Error obteniendo información del repositorio")

    repo_data = repo_response.json()

    # Lenguajes
    languages_response = await get(f"{base_url}/languages", headers)
    languages_data = languages_response.json()
    languages = list(languages_data.keys())

    # Últimos commits
    commits_response = await get(f"{base_url}/commits?per_page=5", headers)
    commits_data = commits_response.json()

    commits = []
    for commit in commits_data:
        commits.append({
            "sha": commit["sha"],
            "message": commit["commit"]["message"],
            "author": commit["commit"]["author"]["name"]
        })

    return {
        "provider": "github",
        "name": repo_data["name"],
        "owner": repo_data["owner"]["login"],
        "description": repo_data["description"],
        "is_private": repo_data["private"],
        "default_branch": repo_data["default_branch"],
        "created_at": repo_data["created_at"],
        "updated_at": repo_data["updated_at"],
        "stars": repo_data["stargazers_count"],
        "forks": repo_data["forks_count"],
        "open_issues": repo_data["open_issues_count"],
        "languages": languages,
        "commits": commits,
        "url": repo_data["html_url"]
    }
