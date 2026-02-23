"""
session_service.py - Gestión de sesiones de usuario

Este servicio es el CORAZÓN del sistema de cookies.
Maneja el almacenamiento y recuperación de sesiones de usuario.

Cada sesión contiene:
- UUID único (el valor de la cookie)
- Historial de búsquedas
- Últimos resultados
- Timestamps de creación y último acceso

⚠️ IMPORTANTE: Las sesiones se guardan en memoria (diccionario Python)
Esto significa que se pierden al reiniciar el servidor.
Para producción, usar Redis, Memcached o base de datos.
"""

# uuid: Librería para generar UUIDs (identificadores únicos universales)
# UUID = Universally Unique Identifier
# Ejemplo: "a3f2c1b4-5678-90ab-cdef-1234567890ab"
import uuid

# Dict: Tipo para diccionarios con tipos específicos
# Any: Tipo que acepta cualquier valor
# Optional: Tipo que puede ser None
from typing import Dict, Any, Optional

# datetime: Para manejar fechas y horas
from datetime import datetime


# ============================================================================
# ALMACÉN DE SESIONES
# ============================================================================
# Diccionario que guarda TODAS las sesiones en memoria
# Estructura:
# {
#     "uuid-sesion-1": {
#         "created_at": "2024-01-15T10:30:00",
#         "last_accessed": "2024-01-15T11:00:00",
#         "searches": [{"query": "fastapi", "timestamp": "...", "results_count": 10}],
#         "last_search_query": "fastapi",
#         "last_results": [...]
#     },
#     "uuid-sesion-2": { ... }
# }
#
# ⚠️ LIMITACIÓN: Este diccionario vive en la RAM del proceso Python
# Si el servidor se reinicia, se pierden todas las sesiones
# Si usas múltiples workers de uvicorn, cada uno tendrá su propio diccionario
#
# SOLUCIÓN PARA PRODUCCIÓN:
# - Usar Redis: redis.set(session_id, json.dumps(data))
# - Usar Memcached: memcached.set(session_id, data)
# - Usar base de datos SQL/NoSQL
sessions_store: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# FUNCIÓN 1: create_session() - Crear nueva sesión
# ============================================================================
def create_session() -> str:
    """
    Crea una nueva sesión y retorna el UUID generado.

    Esta función se llama cuando:
    1. Usuario hace su primera petición (no tiene cookie)
    2. Cookie existe pero la sesión fue eliminada/expiró

    Returns:
        str: UUID de la sesión (ej: "a3f2c1b4-5678-...")
    """
    # uuid.uuid4() genera un UUID versión 4 (aleatorio)
    # Es prácticamente imposible que se repita
    # Ejemplo: "a3f2c1b4-5678-90ab-cdef-1234567890ab"
    # str() lo convierte de objeto UUID a string
    session_id = str(uuid.uuid4())

    # Inicializa los datos de la sesión en el diccionario global
    # Este diccionario se guardará en sessions_store[session_id]
    sessions_store[session_id] = {
        # created_at: Fecha/hora de creación en formato ISO 8601
        # datetime.now() obtiene fecha/hora actual
        # .isoformat() la convierte a string: "2024-01-15T10:30:00.123456"
        "created_at": datetime.now().isoformat(),

        # last_accessed: Última vez que se accedió a esta sesión
        # Se actualiza en cada petición que use la sesión
        "last_accessed": datetime.now().isoformat(),

        # searches: Historial completo de búsquedas
        # Lista de diccionarios con query, timestamp y results_count
        "searches": [],

        # last_search_query: Última búsqueda realizada (acceso rápido)
        # None al inicio porque no ha hecho ninguna búsqueda
        "last_search_query": None,

        # last_search_filters: Últimos filtros aplicados
        "last_search_filters": None,

        # last_results: Últimos resultados obtenidos (acceso rápido)
        # Lista vacía al inicio
        "last_results": []
    }

    # Retorna el UUID para que se establezca como valor de la cookie
    return session_id


# ============================================================================
# FUNCIÓN 2: get_session() - Obtener datos de sesión existente
# ============================================================================
def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene los datos de una sesión existente.

    Args:
        session_id: UUID de la sesión a buscar

    Returns:
        Dict con los datos de la sesión si existe
        None si la sesión no existe
    """
    # Verifica si el session_id existe en el diccionario
    # 'in' es un operador de Python que verifica membresía
    if session_id in sessions_store:
        # Actualiza el timestamp de último acceso
        # Esto permite implementar expiración por inactividad
        sessions_store[session_id]["last_accessed"] = datetime.now().isoformat()

        # Retorna el diccionario completo con todos los datos
        return sessions_store[session_id]

    # Si no existe, retorna None
    # El código que llama a esta función verificará if not get_session(...)
    return None


# ============================================================================
# FUNCIÓN 3: update_session() - Actualizar datos de sesión
# ============================================================================
def update_session(session_id: str, data: Dict[str, Any]) -> None:
    """
    Actualiza los datos de una sesión existente.

    Esta función es genérica para actualizar cualquier campo.
    Actualmente no se usa mucho, pero está disponible para futuras features.

    Args:
        session_id: UUID de la sesión a actualizar
        data: Diccionario con los campos a actualizar
              Ejemplo: {"user_preferences": {"theme": "dark"}}

    Returns:
        None (modifica el diccionario global directamente)
    """
    # Verifica que la sesión exista
    if session_id in sessions_store:
        # .update() fusiona el diccionario 'data' con el existente
        # Si hay claves repetidas, los valores de 'data' sobrescriben
        # Ejemplo:
        # sessions_store[id] = {"a": 1, "b": 2}
        # update({"b": 3, "c": 4})
        # Resultado: {"a": 1, "b": 3, "c": 4}
        sessions_store[session_id].update(data)

        # Actualiza timestamp de último acceso
        sessions_store[session_id]["last_accessed"] = datetime.now().isoformat()


# ============================================================================
# FUNCIÓN 4: save_search_to_session() - Guardar búsqueda realizada
# ============================================================================
def save_search_to_session(session_id: str, query: str, results: list, filters: Optional[dict] = None) -> None:
    """
    Guarda una búsqueda y sus resultados en la sesión del usuario.

    Esta es la función MÁS USADA del servicio.
    Se llama después de cada búsqueda exitosa.

    Guarda los datos de DOS formas:
    1. En el historial completo (searches[])
    2. Como "última búsqueda" para acceso rápido

    Args:
        session_id: UUID de la sesión
        query: Texto que se buscó (ej: "fastapi")
        results: Lista de repositorios encontrados

    Returns:
        None (modifica el diccionario global directamente)
    """
    # Verifica que la sesión exista
    if session_id in sessions_store:
        # Obtiene referencia al diccionario de la sesión
        # Esto es un alias, cualquier modificación afecta sessions_store
        session = sessions_store[session_id]

        # --- PASO 1: Agregar al historial ---
        # append() agrega un elemento al final de la lista
        session["searches"].append({
            # query: Texto que se buscó
            "query": query,

            # filters: Filtros aplicados en esta búsqueda
            "filters": filters,

            # timestamp: Cuándo se realizó la búsqueda
            # Formato ISO: "2024-01-15T10:30:00.123456"
            "timestamp": datetime.now().isoformat(),

            # results_count: Cuántos resultados se encontraron
            # len(results) cuenta elementos de la lista
            "results_count": len(results)
        })

        # --- PASO 2: Guardar como "última búsqueda" ---
        # Esto permite acceso rápido sin iterar por todo el historial
        # Sobrescribe el valor anterior

        # last_search_query: Última query (para mostrar en UI)
        session["last_search_query"] = query

        # last_search_filters: Últimos filtros aplicados
        session["last_search_filters"] = filters

        # last_results: Últimos resultados completos
        # Esto permite mostrar los resultados al reabrir el sitio
        # sin hacer una nueva búsqueda
        session["last_results"] = results

        # Actualiza timestamp de último acceso
        session["last_accessed"] = datetime.now().isoformat()
