"""
Errores de aplicación con formato uniforme.

El diseño exige que todos los errores de la API tengan la misma estructura:
    {"error": {"code": "invalid_credentials", "message": "..."}}
El frontend decide qué mostrar según ``code``; ``message`` es texto amigable
y NUNCA contiene contraseñas ni detalles internos.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Error controlado que se traduce a una respuesta HTTP uniforme."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """Convierte un AppError en la respuesta JSON uniforme."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )