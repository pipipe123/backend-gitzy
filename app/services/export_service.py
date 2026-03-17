"""
export_service.py - Guarda resultados de búsqueda en archivos JSON con timestamp.
"""

import json
import os
from datetime import datetime
from typing import Optional


EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "search_results")


def save_search_results(query: str, results: list, filters: Optional[dict] = None) -> str:
    """Guarda los resultados de búsqueda en un archivo JSON con timestamp.

    Returns:
        Ruta del archivo creado.
    """
    os.makedirs(EXPORT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_{timestamp}.json"
    filepath = os.path.join(EXPORT_DIR, filename)

    data = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "filters": filters,
        "total_results": len(results),
        "results": results,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath
