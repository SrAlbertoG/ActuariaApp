"""
Punto de entrada del backend FastAPI.

El backend no depende de Tauri ni de React. La misma API puede reutilizarse
en una futura modalidad web.
"""

import logging

import uvicorn
from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, invoices, transactions
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler
from app.core.logging import setup_logging
from app.core.security import verify_session_token

log = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Fábrica de la aplicación para facilitar las pruebas automatizadas."""
    settings = get_settings()
    setup_logging()

    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, app_error_handler)

    @app.get("/health", tags=["sistema"])
    def health() -> dict:
        """Endpoint público que Tauri usa para verificar el arranque."""
        return {"status": "ok", "version": settings.app_version}

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {"servicio": settings.app_name, "docs": "/docs", "health": "/health"}

    # Todo lo que cuelga de /api/v1 requiere el token temporal de sesión.
    api_v1 = APIRouter(
        prefix="/api/v1",
        dependencies=[Depends(verify_session_token)],
    )

    @api_v1.get("/ping", tags=["sistema"])
    def ping() -> dict:
        """Endpoint protegido para verificar que el token funciona."""
        return {"pong": True}

    api_v1.include_router(auth.router)
    api_v1.include_router(invoices.router)
    api_v1.include_router(transactions.router)
    app.include_router(api_v1)

    log.info("Backend iniciado (v%s)", settings.app_version)
    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None)
