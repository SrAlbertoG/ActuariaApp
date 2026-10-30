"""Dependencias reutilizables de la API."""

from fastapi import Depends

from app.services.auth_service import AuthService, get_auth_service


def require_sql_connection(
    service: AuthService = Depends(get_auth_service),
) -> AuthService:
    """
    Bloquea el endpoint si no hay sesión activa en SQL Server.

    Todo router que consulte SQL Server (facturas, transacciones, extracción)
    la declarará como dependencia. Así la API cumple el criterio de que no se
    accede a esos módulos sin conexión.
    """
    service.require_connected()
    return service