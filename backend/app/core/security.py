"""
Seguridad de la comunicación local entre Tauri/React y FastAPI.

Aunque el backend solo escucha en 127.0.0.1, otro proceso del mismo equipo
podría intentar llamarlo. Por eso cada petición debe incluir el encabezado
``X-Session-Token`` con el token que Tauri entregó al iniciar el backend.
"""

import secrets

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def verify_session_token(x_session_token: str = Header(default="")) -> None:
    """
    Dependencia de FastAPI que valida el token de sesión.

    Se usa ``compare_digest`` (comparación en tiempo constante) para evitar
    ataques de temporización.
    """
    expected = get_settings().api_token
    if not secrets.compare_digest(x_session_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sesión inválido.",
        )