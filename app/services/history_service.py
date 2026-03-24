"""
history_service.py - Almacén en memoria del historial de análisis por sesión.

Guarda un registro cada vez que se ejecuta un análisis (analyze, AI summary,
code-analysis, suggestions) asociado a la cookie de sesión del usuario.
"""

import uuid
from datetime import datetime
from typing import Any

# { session_id: [ {entry}, {entry}, ... ] }
_history_store: dict[str, list[dict[str, Any]]] = {}

MAX_ENTRIES_PER_SESSION = 50


def save_history_entry(
    session_id: str,
    action: str,
    provider: str | None = None,
    repo_name: str | None = None,
    repo_owner: str | None = None,
    url: str | None = None,
    details: dict | None = None,
) -> str:
    """Guarda una entrada en el historial y devuelve su entry_id."""
    if session_id not in _history_store:
        _history_store[session_id] = []

    entry_id = str(uuid.uuid4())
    entry = {
        "entry_id": entry_id,
        "action": action,
        "provider": provider,
        "repo_name": repo_name,
        "repo_owner": repo_owner,
        "url": url,
        "details": details or {},
        "timestamp": datetime.now().isoformat(),
    }

    entries = _history_store[session_id]
    entries.append(entry)

    # Limitar tamaño
    if len(entries) > MAX_ENTRIES_PER_SESSION:
        _history_store[session_id] = entries[-MAX_ENTRIES_PER_SESSION:]

    return entry_id


def get_history(session_id: str) -> list[dict[str, Any]]:
    """Devuelve el historial completo de una sesión (más reciente primero)."""
    return list(reversed(_history_store.get(session_id, [])))


def get_history_entry(session_id: str, entry_id: str) -> dict[str, Any] | None:
    """Devuelve una entrada específica del historial."""
    for entry in _history_store.get(session_id, []):
        if entry["entry_id"] == entry_id:
            return entry
    return None


def clear_history(session_id: str) -> int:
    """Limpia el historial de una sesión. Devuelve la cantidad de entradas eliminadas."""
    count = len(_history_store.get(session_id, []))
    _history_store.pop(session_id, None)
    return count
