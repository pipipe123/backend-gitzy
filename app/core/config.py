"""
config.py - Configuración global y variables de entorno (Producción)
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITLAB_TOKEN: str = os.getenv("GITLAB_TOKEN", "")
    AZURE_TOKEN: str = os.getenv("AZURE_TOKEN", "")
    AZURE_ORGANIZATION: str = os.getenv("AZURE_ORGANIZATION", "")
    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    COOKIE_NAME: str = "session_id"
    COOKIE_MAX_AGE: int = 30 * 24 * 60 * 60  # 30 days


settings = Settings()
