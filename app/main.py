"""
main.py - Punto de entrada de la aplicación FastAPI

Este archivo inicializa la aplicación FastAPI, configura CORS para permitir
cookies cross-origin y registra los routers con todos los endpoints.

Flujo: Usuario → FastAPI (main.py) → CORS Middleware → Routers → Endpoints
"""

# Importa la clase FastAPI, el framework web asíncrono que usamos
from fastapi import FastAPI

# Importa el middleware de CORS (Cross-Origin Resource Sharing)
# Necesario para que el frontend (distinto dominio) pueda hacer peticiones
from fastapi.middleware.cors import CORSMiddleware

# Importa nuestro router de repository que contiene todos los endpoints
from app.routers import repository

# Crea la instancia principal de la aplicación FastAPI
# Esta es la app que se ejecutará con uvicorn
app = FastAPI(
    title="Repository Analyzer API",  # Nombre mostrado en la documentación de Swagger
    version="1.0.0",  # Versión de la API
    description="API para buscar repositorios en GitHub, GitLab y Azure DevOps con persistencia de sesión"
)

# Configuración del middleware CORS
# CORS = Cross-Origin Resource Sharing
# Permite que navegadores permitan peticiones desde otros dominios (frontend → backend)
app.add_middleware(
    CORSMiddleware,
    # allow_origins: Lista de dominios permitidos para hacer peticiones
    # localhost:3000 = típico de React/Next.js
    # localhost:5173 = típico de Vite
    # En producción, cambiar por el dominio real del frontend
    allow_origins=["http://localhost:3000", "http://localhost:5173"],

    # allow_credentials: CRÍTICO para cookies
    # Debe ser True para que el navegador envíe/reciba cookies en peticiones cross-origin
    # Sin esto, las cookies serán bloqueadas por el navegador
    allow_credentials=True,

    # allow_methods: Permite todos los métodos HTTP (GET, POST, PUT, DELETE, PATCH, OPTIONS)
    # El asterisco (*) significa "todos"
    allow_methods=["*"],

    # allow_headers: Permite todos los headers HTTP
    # Importante para Content-Type, Authorization, etc.
    allow_headers=["*"],
)

# Registra el router de repository
# Esto conecta todos los endpoints definidos en repository.py a la aplicación
# Los endpoints estarán disponibles bajo el prefijo /repository
app.include_router(repository.router)
