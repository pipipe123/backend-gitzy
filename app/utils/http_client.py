"""
http_client.py - Cliente HTTP asíncrono compartido

Este módulo proporciona funciones reutilizables para hacer peticiones HTTP.
Usa httpx, una librería moderna que soporta async/await.

¿Por qué httpx y no requests?
- requests es síncrono (bloquea el servidor mientras espera respuesta)
- httpx es asíncrono (permite manejar múltiples peticiones en paralelo)
- Con async, el servidor puede atender otras peticiones mientras espera HTTP

Ejemplo de uso:
    response = await get("https://api.github.com/users/octocat")
    data = response.json()
"""

# httpx: Librería HTTP moderna con soporte para async/await
# Similar a requests pero con superpoderes asíncronos
import httpx


async def get(url: str, headers: dict = None):
    """
    Realiza una petición HTTP GET asíncrona.

    Esta función es un wrapper sobre httpx.AsyncClient.get()
    para simplificar su uso en toda la aplicación.

    Args:
        url: URL completa a la que hacer la petición
             Ejemplo: "https://api.github.com/repos/user/repo"

        headers: Diccionario opcional con headers HTTP
                 Ejemplo: {"Authorization": "Bearer token123"}
                 Si es None, no se envían headers personalizados

    Returns:
        httpx.Response: Objeto de respuesta con:
            - .status_code: Código HTTP (200, 404, 500, etc.)
            - .json(): Parsea el body como JSON
            - .text: Body como string
            - .headers: Headers de la respuesta

    Ejemplo de uso:
        response = await get("https://api.github.com/users/octocat")
        if response.status_code == 200:
            data = response.json()
            print(data["name"])
    """
    # async with: Context manager asíncrono
    # Asegura que el cliente HTTP se cierre al terminar, liberando recursos
    #
    # ¿Por qué crear un nuevo cliente cada vez?
    # - httpx.AsyncClient() maneja un pool de conexiones HTTP/2
    # - Se cierra automáticamente al salir del 'with'
    # - Alternativa: crear un cliente global y reutilizarlo (más eficiente)
    async with httpx.AsyncClient() as client:
        # client.get(): Hace la petición GET
        # await: Espera la respuesta SIN BLOQUEAR el servidor
        # Mientras espera, Python puede ejecutar otras tareas
        #
        # Ejemplo de concurrencia:
        # task1 = get("https://api.github.com/...")  # Inicia petición
        # task2 = get("https://gitlab.com/api/...")  # Inicia otra petición
        # await task1  # Espera a que task1 termine
        # await task2  # Espera a que task2 termine
        # Ambas peticiones se ejecutan en paralelo, no secuencialmente
        response = await client.get(url, headers=headers)

        # Retorna el objeto Response completo
        # El código que llamó a esta función puede:
        # - Verificar response.status_code
        # - Parsear response.json()
        # - Leer response.text
        return response
