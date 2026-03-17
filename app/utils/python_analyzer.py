"""
python_analyzer.py - Análisis de métricas de código Python usando AST

Calcula:
- Complejidad ciclomática por función
- Líneas por función
- Ratio comentario/código por archivo
"""

import ast


# Nodos AST que incrementan la complejidad ciclomática
_COMPLEXITY_NODES = (
    ast.If, ast.IfExp, ast.For, ast.While,
    ast.ExceptHandler, ast.With, ast.Assert,
)


def _calculate_complexity(node: ast.AST) -> int:
    """Calcula la complejidad ciclomática de un nodo función. Base = 1."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, _COMPLEXITY_NODES):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            # Cada and/or agrega 1 por operador
            complexity += len(child.values) - 1
    return complexity


def _get_docstring_lines(node: ast.AST) -> set:
    """Retorna el conjunto de líneas ocupadas por docstrings en el AST."""
    docstring_lines = set()
    for child in ast.walk(node):
        if not isinstance(child, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if not child.body:
            continue
        first_stmt = child.body[0]
        if (isinstance(first_stmt, ast.Expr)
                and isinstance(first_stmt.value, ast.Constant)
                and isinstance(first_stmt.value.value, str)):
            for line_no in range(first_stmt.lineno, first_stmt.end_lineno + 1):
                docstring_lines.add(line_no)
    return docstring_lines


def _find_functions(tree: ast.Module) -> list:
    """Encuentra todas las funciones/métodos con nombre calificado."""
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append({
                        "name": f"{node.name}.{item.name}",
                        "node": item,
                    })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Solo funciones de nivel módulo (no métodos, ya capturados arriba)
            is_method = False
            for parent in ast.walk(tree):
                if isinstance(parent, ast.ClassDef) and node in parent.body:
                    is_method = True
                    break
            if not is_method:
                functions.append({
                    "name": node.name,
                    "node": node,
                })

    return functions


def _count_lines(source: str, docstring_lines: set) -> dict:
    """Cuenta líneas de comentario, código y en blanco."""
    comment_lines = 0
    blank_lines = 0
    code_lines = 0

    for i, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            blank_lines += 1
        elif stripped.startswith("#"):
            comment_lines += 1
        elif i in docstring_lines:
            comment_lines += 1
        else:
            code_lines += 1

    return {
        "comment_lines": comment_lines,
        "code_lines": code_lines,
        "blank_lines": blank_lines,
    }


def analyze_python_source(source: str) -> dict | None:
    """
    Analiza código fuente Python y retorna métricas.

    Retorna None si el archivo tiene errores de sintaxis.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    docstring_lines = _get_docstring_lines(tree)
    line_counts = _count_lines(source, docstring_lines)

    functions_data = _find_functions(tree)
    functions_metrics = []

    for func_info in functions_data:
        node = func_info["node"]
        line_start = node.lineno
        line_end = node.end_lineno
        lines = line_end - line_start + 1
        complexity = _calculate_complexity(node)

        functions_metrics.append({
            "name": func_info["name"],
            "line_start": line_start,
            "line_end": line_end,
            "lines": lines,
            "cyclomatic_complexity": complexity,
        })

    code_lines = line_counts["code_lines"]
    comment_lines = line_counts["comment_lines"]
    ratio = comment_lines / code_lines if code_lines > 0 else 0.0

    return {
        "functions": functions_metrics,
        "comment_lines": comment_lines,
        "code_lines": code_lines,
        "blank_lines": line_counts["blank_lines"],
        "comment_code_ratio": round(ratio, 4),
    }
