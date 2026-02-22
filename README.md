# Repository Analyzer API

API para buscar y analizar repositorios en GitHub, GitLab y Azure DevOps con persistencia de sesión mediante cookies.

## Características

- 🔍 Búsqueda de repositorios en múltiples proveedores (GitHub, GitLab, Azure DevOps)
- 🍪 Sistema de cookies de sesión para mantener el estado del usuario
- 💾 Persistencia de búsquedas y resultados
- 🔄 Recuperación automática del estado al volver a abrir el sitio

## Instalación

1. Instalar dependencias:
```bash
pip install -r requeriments.text
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus tokens
```

3. Ejecutar el servidor:
```bash
uvicorn app.main:app --reload
```

## Endpoints

### POST /repository/search
Busca repositorios en GitHub, GitLab y Azure DevOps.

**Request:**
```json
{
  "query": "fastapi"
}
```

**Response:**
```json
{
  "query": "fastapi",
  "results": [
    {
      "provider": "github",
      "name": "fastapi",
      "owner": "tiangolo",
      "description": "FastAPI framework",
      "url": "https://github.com/tiangolo/fastapi",
      "stars": 50000,
      "language": "Python",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total_results": 10
}
```

**Nota:** Este endpoint establece automáticamente una cookie de sesión.

### GET /repository/session
Recupera los datos de la sesión actual del usuario.

**Response:**
```json
{
  "session_id": "uuid-de-la-sesion",
  "last_search_query": "fastapi",
  "last_results": [...],
  "searches_count": 5
}
```

### POST /repository/analyze
Analiza un repositorio específico por su URL.

**Request:**
```json
{
  "url": "https://github.com/tiangolo/fastapi"
}
```

## Cómo funciona el sistema de cookies

1. **Primera visita:** Cuando un usuario hace su primera búsqueda, el sistema crea automáticamente una cookie de sesión única.

2. **Cookie de sesión:** La cookie se llama `session_id` y tiene una duración de 30 días.

3. **Persistencia:** Cada búsqueda y sus resultados se guardan asociados a la cookie de sesión.

4. **Retorno:** Cuando el usuario vuelve a abrir el sitio, el navegador envía automáticamente la cookie y el backend puede recuperar:
   - Última búsqueda realizada
   - Últimos resultados
   - Historial de búsquedas

## Configuración del Frontend

Para que las cookies funcionen correctamente con tu frontend, asegúrate de:

1. Incluir `credentials: 'include'` en las peticiones fetch:
```javascript
fetch('http://localhost:8000/repository/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include', // Importante para enviar/recibir cookies
  body: JSON.stringify({ query: 'fastapi' })
})
```

2. El backend ya está configurado con CORS para permitir:
   - `http://localhost:3000` (React/Next.js típico)
   - `http://localhost:5173` (Vite típico)

Si usas otro puerto, agrégalo en [app/main.py](app/main.py) en la configuración de CORS.

## Estructura del Proyecto

```
backend/
├── app/
│   ├── core/
│   │   └── config.py          # Configuración de la app
│   ├── models/
│   │   ├── request_models.py  # Modelos de entrada
│   │   └── response_models.py # Modelos de salida
│   ├── routers/
│   │   └── repository.py      # Endpoints de la API
│   ├── services/
│   │   ├── github_service.py  # Servicio de GitHub (análisis)
│   │   ├── github_search_service.py # Búsqueda en GitHub
│   │   ├── gitlab_service.py  # Búsqueda en GitLab
│   │   ├── azure_service.py   # Búsqueda en Azure DevOps
│   │   ├── session_service.py # Gestión de sesiones
│   │   └── provider_detector.py # Detección de proveedor por URL
│   ├── utils/
│   │   └── http_client.py     # Cliente HTTP asíncrono
│   └── main.py                # Aplicación principal
├── .env                       # Variables de entorno
├── .env.example               # Ejemplo de configuración
└── requeriments.text          # Dependencias
```

## Notas de Desarrollo

- **Almacenamiento:** Actualmente las sesiones se guardan en memoria. Para producción, considera usar Redis o una base de datos.
- **Seguridad:** Cambia `SECRET_KEY` en el archivo `.env` para producción.
- **Tokens:** Los tokens de GitLab y Azure DevOps son opcionales. Sin ellos, esos proveedores no devolverán resultados.
