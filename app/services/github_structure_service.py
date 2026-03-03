from app.core.config import settings
from app.utils.http_client import get
from app.utils.tree_builder import build_nested_tree


async def get_github_structure(repo_info: dict) -> dict:
    owner = repo_info["owner"]
    repo = repo_info["repo"]

    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    # Obtener rama por defecto
    repo_response = await get(base_url, headers)
    if repo_response.status_code != 200:
        raise Exception(f"Error obteniendo información del repositorio: {repo_response.status_code}")

    repo_data = repo_response.json()
    default_branch = repo_data["default_branch"]

    # Obtener árbol recursivo
    tree_url = f"{base_url}/git/trees/{default_branch}?recursive=1"
    tree_response = await get(tree_url, headers)
    if tree_response.status_code != 200:
        raise Exception(f"Error obteniendo árbol del repositorio: {tree_response.status_code}")

    tree_data = tree_response.json()
    flat_items = tree_data.get("tree", [])

    nested_tree, file_count, dir_count = build_nested_tree(flat_items)

    return {
        "provider": "github",
        "owner": owner,
        "name": repo,
        "default_branch": default_branch,
        "total_files": file_count,
        "total_directories": dir_count,
        "tree": nested_tree
    }
