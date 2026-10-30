import logging
import re

import pyodbc

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.connection import AuthType, ConnectionParams

log = logging.getLogger(__name__)

def resolve_driver(preferred: str) -> str:

    installed = pyodbc.drivers()
    if preferred in installed:
        return preferred

    pattern = re.compile(r"ODBC Driver (\d+) for SQL Server")
    candidates = sorted(
        (d for d in installed if pattern.fullmatch(d)),
        key=lambda d: int(pattern.fullmatch(d).group(1)),
        reverse=True,
    )

    if candidates:
        log.warning("Driver '%s' no disponible; se usa '%s'", preferred, candidates[0])
        return candidates[0]

    raise AppError(
        "driver_missing",
        "No se encontro un driver ODBC para SQL Server en este equipo."
        "Solicita a TI la instalacion de 'ODBC Driver 17 for SQL Server'.",
        500,
    )

def build_connection_string(params: ConnectionParams, driver: str) -> str:

    settings = get_settings()
    parts = [f"DRIVER={{{driver}}}",f"SERVER={params.server}"]
    if params.database:
        parts.append(f"DATABASE={params.database}")
    if params.auth_type == AuthType.WINDOWS:
        parts.append("Trusted_Connection=yes")
    else:
        escaped = (params.password or "").replace("}","}}")
        parts.append(f"UID={params.username}")
        parts.append(f"PWD={{{escaped}}}")

    if "OBDC Driver 18" in driver:
        parts.append("Encrypt=yes")
        trust = "yes" if settings.sql_trust_server_certificate else "no"
        parts.append(f"TrustServerCertificate={trust}")

    return ";".join(parts) + ";"

def classify_error(exc: pyodbc.Error) -> AppError:

    sqlstate = str(exc.args[0]) if exc.args else ""
    detail = str(exc.args[1]) if len(exc.args) > 1 else ""
    log.warning("Fallo de conexion a SQL Server (SQLSTATE=%s)", sqlstate)

    if sqlstate == "IM002":
        return AppError("driver_missing","No se encontro el driver ODBC de SQL Server.", 500)

    if "4060" in detail:
        return AppError(
            "permission_error",
            "El usuario no tiene permisos sobre la base de datos indicada.",
            403,
        )

    if "18456" in detail or sqlstate == "28000":
        return AppError("invalid_credentials", "Usuario o contraseña.",401)
    if sqlstate in {"08001","08S01","HYT00"} or "timeout" in detail.lower():
        return AppError(
            "server_unavailable",
            "No se pudo conectar al servidor. Verifica el nombre, la red o la VPN.",
            503,
        )
    return AppError("connection_error","No fue posible establecer la conexión",500)

def open_connection(params: ConnectionParams) -> pyodbc.Connection:
    settings = get_settings()
    driver = resolve_driver(settings.sql_driver)
    conn_str = build_connection_string(params,driver)

    try:
        conn = pyodbc.connect(
            conn_str, timeout=settings.sql_login_timeout, autocommit=True
        )
        conn.cursor().execute("SELECT 1").fetchone()
        return conn
    except pyodbc.Error as exc: 
        raise classify_error(exc) from None
    