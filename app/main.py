"""
main.py - Punto de entrada de la aplicación FastAPI (Producción)
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import repository

app = FastAPI(
    title="Repository Analyzer API",
    version="1.0.0",
    description="API para buscar repositorios en GitHub, GitLab y Azure DevOps con persistencia de sesión",
    docs_url=None if os.getenv("ENVIRONMENT") == "production" else "/docs",
    redoc_url=None if os.getenv("ENVIRONMENT") == "production" else "/redoc",
)

# CORS - Orígenes permitidos desde variable de entorno
# Configurar ALLOWED_ORIGINS con los dominios reales del frontend
# Ejemplo: ALLOWED_ORIGINS=https://gitzy.app,https://www.gitzy.app
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(repository.router)
