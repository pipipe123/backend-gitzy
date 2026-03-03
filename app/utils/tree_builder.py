"""
tree_builder.py - Utilidad para construir árboles de archivos anidados

Transforma listas planas de archivos/carpetas (como las que devuelven las APIs
de GitHub y GitLab) en una estructura de árbol anidada.
"""


def build_nested_tree(flat_items: list) -> tuple:
    """
    Transforma una lista plana en estructura de árbol anidada.

    Args:
        flat_items: Lista de dicts con "path", "type" ("blob"/"tree"), y opcionalmente "size"

    Returns:
        Tupla de (nested_tree_list, file_count, directory_count)
    """
    file_count = 0
    dir_count = 0
    dir_map = {}
    root_children = []

    sorted_items = sorted(flat_items, key=lambda x: x["path"])

    for item in sorted_items:
        path = item["path"]
        item_type = item.get("type", "blob")
        parts = path.split("/")
        name = parts[-1]

        if item_type == "blob":
            node = {
                "name": name,
                "path": path,
                "type": "file",
                "size": item.get("size"),
                "children": None
            }
            file_count += 1
        elif item_type == "tree":
            node = {
                "name": name,
                "path": path,
                "type": "directory",
                "size": None,
                "children": []
            }
            dir_map[path] = node
            dir_count += 1
        else:
            continue

        if len(parts) == 1:
            root_children.append(node)
        else:
            parent_path = "/".join(parts[:-1])
            if parent_path in dir_map:
                dir_map[parent_path]["children"].append(node)
            else:
                _ensure_parents(dir_map, root_children, parent_path)
                dir_map[parent_path]["children"].append(node)

    return root_children, file_count, dir_count


def _ensure_parents(dir_map: dict, root_children: list, path: str):
    """
    Crea directorios padres faltantes en el árbol.
    Maneja casos donde la API no devuelve entradas explícitas para directorios intermedios.
    """
    parts = path.split("/")
    for i in range(len(parts)):
        partial_path = "/".join(parts[:i + 1])
        if partial_path not in dir_map:
            node = {
                "name": parts[i],
                "path": partial_path,
                "type": "directory",
                "size": None,
                "children": []
            }
            dir_map[partial_path] = node
            if i == 0:
                root_children.append(node)
            else:
                parent_path = "/".join(parts[:i])
                if parent_path in dir_map:
                    dir_map[parent_path]["children"].append(node)
