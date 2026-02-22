"""
provider_detector.py - Detector de proveedor de repositorios

Este módulo analiza URLs de repositorios y determina:
1. ¿De qué proveedor es? (GitHub, GitLab, Azure DevOps)
2. ¿Cuál es el owner (dueño)?
3. ¿Cuál es el nombre del repositorio?

Ejemplo de URLs soportadas:
- GitHub: https://github.com/tiangolo/fastapi
- GitHub: https://github.com/microsoft/vscode/tree/main
- GitLab: https://gitlab.com/gitlab-org/gitlab (futuro)
- Azure: https://dev.azure.com/org/project/_git/repo (futuro)
"""

# urllib.parse: Librería estándar de Python para parsear URLs
# urlparse() descompone una URL en sus componentes
from urllib.parse import urlparse


def detect_provider(url: str):
    """
    Detecta el proveedor de un repositorio a partir de su URL.

    Args:
        url: URL completa del repositorio
             Ejemplo: "https://github.com/tiangolo/fastapi"

    Returns:
        Tupla (proveedor, info):
        - proveedor: "github", "gitlab", "azure" o None
        - info: Diccionario con "owner" y "repo", o None

    Ejemplos:
        >>> detect_provider("https://github.com/user/repo")
        ("github", {"owner": "user", "repo": "repo"})

        >>> detect_provider("https://example.com/unknown")
        (None, None)
    """
    # urlparse() descompone la URL en componentes
    # Ejemplo: "https://github.com/owner/repo/tree/main"
    # parsed.scheme = "https"
    # parsed.netloc = "github.com"
    # parsed.path = "/owner/repo/tree/main"
    # parsed.query = ""
    # parsed.fragment = ""
    parsed = urlparse(url)

    # --- Detector de GitHub ---
    # Verifica si el dominio contiene "github.com"
    # parsed.netloc = dominio (ej: "github.com", "api.github.com")
    if "github.com" in parsed.netloc:
        # Extrae las partes del path
        # Ejemplo: "/owner/repo/tree/main"
        # .strip("/") quita las barras de los extremos: "owner/repo/tree/main"
        # .split("/") divide por barras: ["owner", "repo", "tree", "main"]
        parts = parsed.path.strip("/").split("/")

        # Verificamos que haya al menos 2 partes (owner y repo)
        # parts[0] = owner (usuario u organización)
        # parts[1] = repo (nombre del repositorio)
        # parts[2+] = pueden ser "tree", "blob", "issues", etc. (los ignoramos)
        if len(parts) >= 2:
            # Retorna tupla con el proveedor y la info extraída
            return "github", {
                "owner": parts[0],  # Primera parte = dueño
                "repo": parts[1]    # Segunda parte = repositorio
            }

    # --- Detectores futuros ---
    # Aquí se pueden agregar detectores para otros proveedores:
    #
    # if "gitlab.com" in parsed.netloc:
    #     # Lógica similar para GitLab
    #     # GitLab puede tener grupos anidados: gitlab.com/group/subgroup/project
    #     pass
    #
    # if "dev.azure.com" in parsed.netloc:
    #     # Azure DevOps tiene estructura diferente:
    #     # dev.azure.com/{organization}/{project}/_git/{repository}
    #     pass

    # Si no coincide con ningún proveedor conocido, retorna None
    return None, None