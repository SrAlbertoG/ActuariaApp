"""
Servicio de autenticación contra SQL Server.

Mantiene en MEMORIA los parámetros de la sesión activa (nunca se persiste el
objeto de conexión). Los repositorios pedirán conexiones mediante
``connection()``, que abre una nueva y la cierra al terminar.
"""

import logging
import threading
from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

import pyodbc

from app.core.credential_store import CredentialStore
from app.core.errors import AppError
from app.integrations.sql_server import connection as sql
from app.models.connection import ConnectionParams
from app.schemas.auth import SavedProfile, SessionStatus

log = logging.getLogger(__name__)


class AuthService:
    """Orquesta login, reconexión automática, recordar y cierre de sesión."""

    def __init__(self, store: CredentialStore | None = None) -> None:
        self._store = store or CredentialStore()
        self._params: ConnectionParams | None = None
        self._lock = threading.Lock()

    # ---- Sesión ----------------------------------------------------------
    def login(self, params: ConnectionParams) -> None:
        """Valida la conexión real y, si funciona, activa la sesión."""
        conn = sql.open_connection(params)  # lanza AppError si falla
        conn.close()
        with self._lock:
            self._params = params
        log.info("Sesión SQL Server iniciada (servidor=%s)", params.server)

    def auto_login(self) -> None:
        """
        Reconexión automática al iniciar la aplicación.

        Si no hay credenciales guardadas no hace nada. Si hay y la conexión
        falla, lanza el error pero CONSERVA las credenciales: el fallo puede
        ser temporal (VPN caída). El usuario decide si las elimina.
        """
        saved = self._store.load()
        if saved is None:
            return
        self.login(saved)

    def logout(self) -> None:
        """Cierra la sesión en memoria. No borra las credenciales guardadas."""
        with self._lock:
            self._params = None
        log.info("Sesión SQL Server cerrada")

    # ---- Credenciales recordadas -----------------------------------------
    def remember(self) -> None:
        """Guarda las credenciales de la sesión ACTIVA (no se reenvía la contraseña)."""
        self._store.save(self.require_connected())

    def forget_credentials(self) -> None:
        self._store.delete()

    # ---- Consulta de estado ----------------------------------------------
    def require_connected(self) -> ConnectionParams:
        """Devuelve los parámetros de la sesión o lanza ``not_connected``."""
        with self._lock:
            params = self._params
        if params is None:
            raise AppError(
                "not_connected", "No hay una conexión activa con SQL Server.", 401
            )
        return params

    def status(self) -> SessionStatus:
        saved = self._store.load()
        profile = (
            SavedProfile(
                server=saved.server,
                database=saved.database,
                auth_type=saved.auth_type,
                username=saved.username,
            )
            if saved
            else None
        )
        with self._lock:
            p = self._params
        return SessionStatus(
            connected=p is not None,
            server=p.server if p else None,
            database=p.database if p else None,
            username=p.username if p else None,
            auth_type=p.auth_type if p else None,
            has_saved_credentials=saved is not None,
            saved_profile=profile,
        )

    # ---- Uso por repositorios --------------------------------------------
    @contextmanager
    def connection(self) -> Iterator[pyodbc.Connection]:
        """Entrega una conexión nueva y garantiza su cierre."""
        conn = sql.open_connection(self.require_connected())
        try:
            yield conn
        finally:
            conn.close()


@lru_cache
def get_auth_service() -> AuthService:
    """Instancia única por proceso (una sesión por instalación local)."""
    return AuthService()