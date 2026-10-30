"""
Seguridad de la comunicación local entre la interfaz y FastAPI.

Cada petición a /api/v1 debe incluir el encabezado ``X-Session-Token`` con el
token que entregó el proceso lanzador (Tauri) al iniciar el backend.
"""

import secrets

from fastapi import Security
from fastapi.security import APIKeyHeader

from app.core.config import get_settings
from app.core.errors import AppError

# auto_error=False: el error lo generamos nosotros con formato uniforme.
_token_header = APIKeyHeader(name="X-Session-Token", auto_error=False)


def verify_session_token(token: str | None = Security(_token_header)) -> None:
    """Valida el token de sesión usando comparación en tiempo constante."""
    expected = get_settings().api_token
    if not token or not secrets.compare_digest(token.encode(), expected.encode()):
        raise AppError("invalid_token", "Token de sesión inválido.", 401)