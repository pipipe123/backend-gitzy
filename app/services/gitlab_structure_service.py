from urllib.parse import quote

from app.core.config import settings
from app.utils.http_client import get
from app.utils.tree_builder import build_nested_tree


async def get_gitlab_structure(repo_info: dict) -> dict:
    owner = repo_info["owner"]
    repo = repo_info["repo"]

    headers = {}
    if settings.GITLAB_TOKEN:
        headers["PRIVATE-TOKEN"] = settings.GITLAB_TOKEN

    project_path = quote(f"{owner}/{repo}", safe="")

    # Obtener info del proyecto (rama por defecto)
    project_url = f"https://gitlab.com/api/v4/projects/{project_path}"
    project_response = await get(project_url, headers if headers else None)
    if project_response.status_code != 200:
        raise Exception(f"Error obteniendo proyecto de GitLab: {project_response.status_code}")

    project_data = project_response.json()
    default_branch = project_data.get("default_branch", "main")

    # Obtener árbol recursivo con paginación
    all_items = []
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
            raise Exception(f"Error obteniendo árbol de GitLab: {tree_response.status_code}")

        items = tree_response.json()
        if not items:
            break

        all_items.extend(items)
        page += 1

        if page > 50:
            break

    # Normalizar formato al esperado por build_nested_tree
    normalized_items = [
        {
            "path": item.get("path", ""),
            "type": item.get("type", "blob"),
            "size": None
        }
        for item in all_items
    ]

    nested_tree, file_count, dir_count = build_nested_tree(normalized_items)

    return {
        "provider": "gitlab",
        "owner": owner,
        "name": repo,
        "default_branch": default_branch,
        "total_files": file_count,
        "total_directories": dir_count,
        "tree": nested_tree
    }
