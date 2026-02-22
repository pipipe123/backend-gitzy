# 🌐 Documentación de Endpoints - Repository Analyzer API

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [URL Base](#url-base)
3. [Sistema de Cookies](#sistema-de-cookies)
4. [Endpoint 1: POST /repository/search](#endpoint-1-post-repositorysearch)
5. [Endpoint 2: GET /repository/session](#endpoint-2-get-repositorysession)
6. [Endpoint 3: POST /repository/analyze](#endpoint-3-post-repositoryanalyze)
7. [Flujos Completos](#flujos-completos)
8. [Códigos de Error](#códigos-de-error)
9. [Ejemplos con cURL](#ejemplos-con-curl)
10. [Ejemplos con JavaScript](#ejemplos-con-javascript)

---

## 🎯 Introducción

Esta API permite buscar y analizar repositorios de código en GitHub, GitLab y Azure DevOps.

**Características principales:**
- ✅ Búsqueda multi-proveedor (GitHub, GitLab, Azure DevOps)
- ✅ Persistencia de sesión mediante cookies
- ✅ Sin necesidad de login/registro
- ✅ Análisis detallado de repositorios individuales

---

## 🔗 URL Base

**Desarrollo:**
```
http://localhost:8000
```

**Producción:**
```
https://tu-dominio.com
```

**Documentación interactiva (Swagger):**
```
http://localhost:8000/docs
```

---

## 🍪 Sistema de Cookies

### ¿Cómo funciona?

La API usa cookies para mantener el estado del usuario **sin necesidad de autenticación**.

#### Cookie: `session_id`

| Propiedad | Valor |
|-----------|-------|
| **Nombre** | `session_id` |
| **Tipo** | UUID v4 (ej: `a3f2c1b4-5678-90ab-cdef-1234567890ab`) |
| **Duración** | 30 días |
| **Seguridad** | `httponly=true`, `samesite=lax` |
| **Creación** | Automática en la primera petición |

#### ¿Qué se guarda en la sesión?

```json
{
  "created_at": "2024-01-15T10:30:00",
  "last_accessed": "2024-01-15T11:00:00",
  "searches": [
    {
      "query": "fastapi",
      "timestamp": "2024-01-15T10:35:00",
      "results_count": 15
    }
  ],
  "last_search_query": "fastapi",
  "last_results": [...]
}
```

#### Flujo de la Cookie

```
1. Primera visita
   Usuario → Backend
   Backend → Genera UUID → Crea sesión → Establece cookie
   Backend → Usuario (con Set-Cookie: session_id=...)

2. Visitas posteriores
   Usuario → Backend (con Cookie: session_id=...)
   Backend → Lee cookie → Recupera sesión → Devuelve datos guardados

3. Usuario cierra navegador y vuelve
   Usuario → Backend (navegador envía cookie automáticamente)
   Backend → Reconoce sesión → Muestra última búsqueda
```

---

## 🔍 Endpoint 1: POST /repository/search

### Descripción

Busca repositorios en GitHub, GitLab y Azure DevOps que coincidan con el texto ingresado.

### URL

```
POST /repository/search
```

### Headers

```http
Content-Type: application/json
Cookie: session_id=<uuid>  # Opcional, se crea automáticamente si no existe
```

### Request Body

```json
{
  "query": "fastapi"
}
```

#### Parámetros

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `query` | string | ✅ Sí | Texto a buscar en repositorios |

### Response

**Status Code:** `200 OK`

```json
{
  "query": "fastapi",
  "total_results": 15,
  "results": [
    {
      "provider": "github",
      "name": "fastapi",
      "owner": "tiangolo",
      "description": "FastAPI framework, high performance...",
      "url": "https://github.com/tiangolo/fastapi",
      "stars": 68000,
      "language": "Python",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "provider": "gitlab",
      "name": "fastapi-example",
      "owner": "gitlab-org",
      "description": "Example FastAPI project",
      "url": "https://gitlab.com/gitlab-org/fastapi-example",
      "stars": 1200,
      "language": null,
      "updated_at": "2024-01-10T15:20:00Z"
    }
  ]
}
```

#### Campos de la Respuesta

**Nivel raíz:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `query` | string | Echo del texto buscado |
| `total_results` | integer | Número total de repositorios encontrados |
| `results` | array | Lista de repositorios |

**Objeto `result`:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `provider` | string | Proveedor: `"github"`, `"gitlab"`, `"azure"` |
| `name` | string | Nombre del repositorio |
| `owner` | string | Dueño (usuario u organización) |
| `description` | string\|null | Descripción del repositorio |
| `url` | string | URL para acceder al repositorio |
| `stars` | integer | Número de estrellas/favoritos |
| `language` | string\|null | Lenguaje principal |
| `updated_at` | string | Fecha de última actualización (ISO 8601) |

### Comportamiento

1. **Si no hay cookie:** Crea nueva sesión y establece cookie
2. **Si hay cookie:** Usa sesión existente
3. **Búsqueda:** Busca en paralelo en GitHub, GitLab y Azure DevOps
4. **Almacenamiento:** Guarda query y resultados en la sesión
5. **Respuesta:** Devuelve repositorios ordenados por estrellas

### Ejemplo completo

```bash
# Primera petición (sin cookie)
curl -X POST http://localhost:8000/repository/search \
  -H "Content-Type: application/json" \
  -d '{"query": "fastapi"}' \
  -c cookies.txt  # Guarda la cookie

# Segunda petición (con cookie guardada)
curl -X POST http://localhost:8000/repository/search \
  -H "Content-Type: application/json" \
  -d '{"query": "django"}' \
  -b cookies.txt  # Envía la cookie guardada
```

---

## 📊 Endpoint 2: GET /repository/session

### Descripción

Obtiene los datos de la sesión del usuario: última búsqueda, resultados guardados e historial.

### URL

```
GET /repository/session
```

### Headers

```http
Cookie: session_id=<uuid>  # Opcional, se crea si no existe
```

### Request Body

No requiere body.

### Response

**Status Code:** `200 OK`

```json
{
  "session_id": "a3f2c1b4-5678-90ab-cdef-1234567890ab",
  "last_search_query": "fastapi",
  "searches_count": 5,
  "last_results": [
    {
      "provider": "github",
      "name": "fastapi",
      "owner": "tiangolo",
      "description": "FastAPI framework...",
      "url": "https://github.com/tiangolo/fastapi",
      "stars": 68000,
      "language": "Python",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Campos de la Respuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `session_id` | string | UUID de la sesión actual |
| `last_search_query` | string\|null | Última búsqueda realizada |
| `searches_count` | integer | Total de búsquedas realizadas |
| `last_results` | array | Últimos resultados obtenidos |

### Comportamiento

1. **Sin cookie existente:**
   - Crea nueva sesión
   - Establece cookie
   - Devuelve sesión vacía (`last_search_query: null`, `last_results: []`)

2. **Con cookie existente:**
   - Recupera sesión guardada
   - Devuelve última búsqueda y resultados
   - Actualiza timestamp de último acceso

### Caso de Uso

**Persistencia al reabrir el sitio:**

```javascript
// Frontend: Al cargar la página
fetch('http://localhost:8000/repository/session', {
  credentials: 'include'  // ← Envía cookie automáticamente
})
.then(res => res.json())
.then(data => {
  if (data.last_search_query) {
    // Usuario tiene búsquedas guardadas
    console.log(`Última búsqueda: ${data.last_search_query}`);
    console.log(`Resultados: ${data.last_results.length}`);
    // Mostrar resultados guardados en la UI
  } else {
    // Usuario nuevo o sin búsquedas
    console.log('Sin búsquedas previas');
  }
});
```

---

## 📝 Endpoint 3: POST /repository/analyze

### Descripción

Analiza UN repositorio específico en detalle usando su URL. Devuelve información completa: commits, lenguajes, estadísticas, etc.

### URL

```
POST /repository/analyze
```

### Headers

```http
Content-Type: application/json
```

**Nota:** Este endpoint NO usa cookies (no necesita persistencia).

### Request Body

```json
{
  "url": "https://github.com/tiangolo/fastapi"
}
```

#### Parámetros

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `url` | string (URL válida) | ✅ Sí | URL completa del repositorio |

**URLs soportadas:**
- ✅ `https://github.com/user/repo`
- ✅ `https://github.com/org/repo/tree/main`
- ✅ `https://github.com/user/repo/issues`
- ❌ URLs de GitLab/Azure (futuro)

### Response

**Status Code:** `200 OK`

```json
{
  "provider": "github",
  "name": "fastapi",
  "owner": "tiangolo",
  "description": "FastAPI framework, high performance, easy to learn...",
  "is_private": false,
  "default_branch": "master",
  "created_at": "2018-12-05T13:05:32Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "stars": 68000,
  "forks": 5800,
  "open_issues": 120,
  "languages": ["Python", "JavaScript", "HTML"],
  "commits": [
    {
      "sha": "a3f2c1b4567890abcdef",
      "message": "Fix bug in dependency injection",
      "author": "Sebastián Ramírez"
    },
    {
      "sha": "b4e3d2c5678901bcdef0",
      "message": "Update documentation",
      "author": "Jane Doe"
    }
  ],
  "url": "https://github.com/tiangolo/fastapi"
}
```

#### Campos de la Respuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `provider` | string | Proveedor: `"github"` |
| `name` | string | Nombre del repositorio |
| `owner` | string | Dueño (usuario u organización) |
| `description` | string\|null | Descripción del repositorio |
| `is_private` | boolean | `true` si es privado, `false` si es público |
| `default_branch` | string | Rama principal (`main`, `master`, etc.) |
| `created_at` | string | Fecha de creación (ISO 8601) |
| `updated_at` | string | Fecha de última actualización (ISO 8601) |
| `stars` | integer | Número de estrellas |
| `forks` | integer | Número de forks |
| `open_issues` | integer | Issues abiertos |
| `languages` | array[string] | Lista de lenguajes usados |
| `commits` | array[object] | Últimos 5 commits |
| `url` | string | URL del repositorio |

**Objeto `commit`:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `sha` | string | Hash único del commit |
| `message` | string | Mensaje del commit |
| `author` | string\|null | Nombre del autor |

### Errores

**Error 400 - URL no soportada:**
```json
{
  "detail": "URL no soportada. Solo se admiten repositorios de GitHub."
}
```

**Error 500 - Repositorio no existe:**
```json
{
  "detail": "Error al analizar el repositorio: Repository not found"
}
```

---

## 🔄 Flujos Completos

### Flujo 1: Usuario Nuevo - Primera Búsqueda

```
1. Usuario abre el frontend
   └─> GET /repository/session
       ├─> Backend: No hay cookie
       ├─> Backend: Crea sesión (UUID: abc123)
       ├─> Backend: Set-Cookie: session_id=abc123
       └─> Response: {session_id: "abc123", last_search_query: null, ...}

2. Usuario busca "fastapi"
   └─> POST /repository/search {"query": "fastapi"}
       Headers: Cookie: session_id=abc123
       ├─> Backend: Busca en GitHub → 10 resultados
       ├─> Backend: Busca en GitLab → 5 resultados
       ├─> Backend: Busca en Azure → 0 resultados
       ├─> Backend: Guarda en sesión abc123
       └─> Response: {query: "fastapi", results: [...15 repos...]}

3. Usuario cierra el navegador
   └─> Cookie se guarda en el navegador

4. Usuario vuelve a abrir el sitio (al día siguiente)
   └─> GET /repository/session
       Headers: Cookie: session_id=abc123 (automático)
       ├─> Backend: Recupera sesión abc123
       └─> Response: {
             session_id: "abc123",
             last_search_query: "fastapi",
             last_results: [...15 repos...]
           }

5. Frontend muestra los resultados guardados
   └─> Usuario ve su búsqueda anterior automáticamente
```

### Flujo 2: Análisis Detallado de un Repositorio

```
1. Usuario hace clic en un repositorio de los resultados
   └─> Frontend obtiene la URL: https://github.com/tiangolo/fastapi

2. Frontend hace petición de análisis
   └─> POST /repository/analyze
       Body: {"url": "https://github.com/tiangolo/fastapi"}
       ├─> Backend: Detecta proveedor → GitHub
       ├─> Backend: Extrae owner=tiangolo, repo=fastapi
       ├─> Backend: Llama a GitHub API (3 peticiones):
       │   ├─> GET /repos/tiangolo/fastapi
       │   ├─> GET /repos/tiangolo/fastapi/languages
       │   └─> GET /repos/tiangolo/fastapi/commits?per_page=5
       └─> Response: {
             provider: "github",
             name: "fastapi",
             owner: "tiangolo",
             languages: ["Python", "JavaScript"],
             commits: [...],
             stars: 68000,
             ...
           }

3. Frontend muestra información detallada
   └─> Usuario ve commits recientes, lenguajes, stats, etc.
```

### Flujo 3: Múltiples Búsquedas en una Sesión

```
1. Búsqueda 1: "fastapi"
   └─> POST /repository/search {"query": "fastapi"}
       └─> Sesión: {
             searches: [
               {query: "fastapi", timestamp: "...", results_count: 15}
             ],
             last_search_query: "fastapi"
           }

2. Búsqueda 2: "django"
   └─> POST /repository/search {"query": "django"}
       └─> Sesión: {
             searches: [
               {query: "fastapi", ...},
               {query: "django", timestamp: "...", results_count: 12}
             ],
             last_search_query: "django"
           }

3. Búsqueda 3: "react"
   └─> POST /repository/search {"query": "react"}
       └─> Sesión: {
             searches: [
               {query: "fastapi", ...},
               {query: "django", ...},
               {query: "react", timestamp: "...", results_count: 20}
             ],
             last_search_query: "react"
           }

4. Usuario consulta su sesión
   └─> GET /repository/session
       └─> Response: {
             searches_count: 3,
             last_search_query: "react",
             last_results: [...20 repos de react...]
           }
```

---

## ⚠️ Códigos de Error

### 400 Bad Request

**Causa:** Datos de entrada inválidos

**Ejemplo 1 - URL inválida:**
```json
Request: {"url": "not-a-valid-url"}
Response: {
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "invalid or missing URL scheme",
      "type": "value_error.url.scheme"
    }
  ]
}
```

**Ejemplo 2 - Query vacío:**
```json
Request: {"query": ""}
Response: {
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### 422 Unprocessable Entity

**Causa:** Request body con estructura incorrecta

**Ejemplo:**
```json
Request: {"wrong_field": "value"}
Response: {
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

**Causa:** Error en el servidor o APIs externas

**Ejemplo:**
```json
Response: {
  "detail": "Error al analizar el repositorio: API rate limit exceeded"
}
```

---

## 🔧 Ejemplos con cURL

### Búsqueda de repositorios

```bash
# Búsqueda simple
curl -X POST http://localhost:8000/repository/search \
  -H "Content-Type: application/json" \
  -d '{"query": "fastapi"}'

# Búsqueda con cookies (guardar sesión)
curl -X POST http://localhost:8000/repository/search \
  -H "Content-Type: application/json" \
  -d '{"query": "fastapi"}' \
  -c cookies.txt \
  -v  # Ver headers (incluye Set-Cookie)

# Búsqueda usando sesión guardada
curl -X POST http://localhost:8000/repository/search \
  -H "Content-Type: application/json" \
  -d '{"query": "django"}' \
  -b cookies.txt  # Envía cookie guardada
```

### Obtener sesión

```bash
# Sin cookie (crea nueva sesión)
curl -X GET http://localhost:8000/repository/session \
  -c cookies.txt

# Con cookie (recupera sesión existente)
curl -X GET http://localhost:8000/repository/session \
  -b cookies.txt
```

### Analizar repositorio

```bash
# Análisis de repositorio de GitHub
curl -X POST http://localhost:8000/repository/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/tiangolo/fastapi"}'

# Pretty print con jq
curl -X POST http://localhost:8000/repository/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/django/django"}' \
  | jq '.'
```

---

## 💻 Ejemplos con JavaScript

### Fetch API (Navegador)

```javascript
// ============================================
// Ejemplo 1: Búsqueda de repositorios
// ============================================
async function searchRepositories(query) {
  try {
    const response = await fetch('http://localhost:8000/repository/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',  // ← CRÍTICO: Envía/recibe cookies
      body: JSON.stringify({ query })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log(`Encontrados ${data.total_results} repositorios`);
    console.log(data.results);
    return data;
  } catch (error) {
    console.error('Error buscando repositorios:', error);
  }
}

// Uso
searchRepositories('fastapi');


// ============================================
// Ejemplo 2: Obtener sesión (al cargar página)
// ============================================
async function loadSession() {
  try {
    const response = await fetch('http://localhost:8000/repository/session', {
      credentials: 'include'  // ← Envía cookie automáticamente
    });

    const data = await response.json();

    if (data.last_search_query) {
      console.log('Sesión encontrada!');
      console.log(`Última búsqueda: ${data.last_search_query}`);
      console.log(`Total de búsquedas: ${data.searches_count}`);
      // Mostrar resultados guardados en la UI
      return data.last_results;
    } else {
      console.log('Usuario nuevo o sin búsquedas');
      return null;
    }
  } catch (error) {
    console.error('Error cargando sesión:', error);
  }
}

// Llamar al cargar la página
window.addEventListener('DOMContentLoaded', loadSession);


// ============================================
// Ejemplo 3: Analizar repositorio específico
// ============================================
async function analyzeRepository(url) {
  try {
    const response = await fetch('http://localhost:8000/repository/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    const data = await response.json();
    console.log(`Repositorio: ${data.name}`);
    console.log(`Estrellas: ${data.stars}`);
    console.log(`Lenguajes: ${data.languages.join(', ')}`);
    console.log(`Últimos commits:`, data.commits);
    return data;
  } catch (error) {
    console.error('Error analizando repositorio:', error);
  }
}

// Uso
analyzeRepository('https://github.com/tiangolo/fastapi');


// ============================================
// Ejemplo 4: App completa (React-style)
// ============================================
class RepositorySearchApp {
  constructor() {
    this.baseURL = 'http://localhost:8000';
  }

  async init() {
    // Cargar sesión al iniciar
    const session = await this.getSession();
    if (session && session.last_results.length > 0) {
      this.displayResults(session.last_results);
    }
  }

  async getSession() {
    const response = await fetch(`${this.baseURL}/repository/session`, {
      credentials: 'include'
    });
    return response.json();
  }

  async search(query) {
    const response = await fetch(`${this.baseURL}/repository/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ query })
    });
    const data = await response.json();
    this.displayResults(data.results);
    return data;
  }

  async analyze(url) {
    const response = await fetch(`${this.baseURL}/repository/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    return response.json();
  }

  displayResults(results) {
    console.log('Mostrando resultados:', results);
    // Aquí iría la lógica para actualizar el DOM
  }
}

// Uso
const app = new RepositorySearchApp();
app.init();  // Carga sesión guardada
app.search('fastapi');  // Busca repositorios
```

### Axios (Node.js/React)

```javascript
import axios from 'axios';

// Configurar axios para usar cookies
const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true  // ← Habilita cookies
});

// Búsqueda
async function search(query) {
  try {
    const { data } = await api.post('/repository/search', { query });
    console.log(data.results);
    return data;
  } catch (error) {
    console.error(error.response?.data || error.message);
  }
}

// Obtener sesión
async function getSession() {
  try {
    const { data } = await api.get('/repository/session');
    return data;
  } catch (error) {
    console.error(error.response?.data || error.message);
  }
}

// Analizar
async function analyze(url) {
  try {
    const { data } = await api.post('/repository/analyze', { url });
    return data;
  } catch (error) {
    console.error(error.response?.data || error.message);
  }
}
```

---

## 🎯 Casos de Uso Reales

### Caso 1: Aplicación de Descubrimiento de Proyectos

```javascript
// Usuario busca proyectos de IA
await searchRepositories('artificial intelligence');

// Usuario encuentra un proyecto interesante y quiere detalles
await analyzeRepository('https://github.com/openai/gpt-3');

// Usuario cierra la app
// ...días después...

// Usuario vuelve y ve su última búsqueda automáticamente
const session = await loadSession();
// Muestra resultados de 'artificial intelligence' guardados
```

### Caso 2: Comparador de Frameworks

```javascript
// Buscar frameworks web
const pythonFrameworks = await searchRepositories('python web framework');
const jsFrameworks = await searchRepositories('javascript web framework');

// Analizar los más populares
const fastapi = await analyzeRepository('https://github.com/tiangolo/fastapi');
const django = await analyzeRepository('https://github.com/django/django');
const express = await analyzeRepository('https://github.com/expressjs/express');

// Comparar estrellas, commits recientes, lenguajes, etc.
console.log({
  fastapi: { stars: fastapi.stars, commits: fastapi.commits.length },
  django: { stars: django.stars, commits: django.commits.length },
  express: { stars: express.stars, commits: express.commits.length }
});
```

### Caso 3: Dashboard de Proyectos Guardados

```javascript
// Obtener historial de búsquedas del usuario
const session = await getSession();

// Mostrar últimas 5 búsquedas
session.last_results.slice(0, 5).forEach(repo => {
  console.log(`${repo.name} (${repo.stars}⭐) - ${repo.url}`);
});
```

---

## 📚 Recursos Adicionales

- **Documentación Interactiva:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Repositorio del Proyecto:** (tu repositorio)
- **GitHub API Docs:** https://docs.github.com/en/rest
- **GitLab API Docs:** https://docs.gitlab.com/ee/api/

---

## ✅ Checklist de Integración

### Frontend

- [ ] Configurar `credentials: 'include'` en todas las peticiones
- [ ] Llamar a `/repository/session` al cargar la página
- [ ] Manejar errores 400, 422, 500
- [ ] Mostrar resultados guardados si existen
- [ ] Implementar UI para búsqueda
- [ ] Implementar UI para análisis detallado

### Backend

- [ ] Configurar tokens en `.env` (GITHUB_TOKEN, GITLAB_TOKEN, etc.)
- [ ] Actualizar `allow_origins` en CORS con el dominio del frontend
- [ ] Configurar SECRET_KEY seguro en producción
- [ ] Implementar rate limiting (opcional)
- [ ] Migrar sesiones a Redis/DB para producción (opcional)

---

## 🐛 Troubleshooting

### Problema: Cookies no se guardan

**Solución:**
```javascript
// ❌ Incorrecto
fetch('http://localhost:8000/repository/search', {
  method: 'POST',
  body: JSON.stringify({ query: 'test' })
});

// ✅ Correcto
fetch('http://localhost:8000/repository/search', {
  method: 'POST',
  credentials: 'include',  // ← Esto es CRÍTICO
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'test' })
});
```

### Problema: Error de CORS

**Solución:** Agregar el dominio del frontend en `app/main.py`:
```python
allow_origins=[
    "http://localhost:3000",  # React
    "http://localhost:5173",  # Vite
    "https://tu-dominio.com"  # Producción
]
```

### Problema: Sesión se pierde al reiniciar servidor

**Causa:** Las sesiones están en memoria (RAM).

**Solución:** Implementar Redis o base de datos para persistencia.

---

¿Listo para empezar? 🚀
