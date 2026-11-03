"""
Persistencia segura de credenciales con el Administrador de credenciales de
Windows (vía la librería ``keyring``).

Se guarda UNA entrada con los datos de conexión en JSON. Ese JSON vive dentro
del almacén cifrado del sistema operativo, por usuario de Windows; nunca en
SQLite, .env, config.py ni Excel (regla de negocio #11).
"""

import json
import logging

import keyring
from keyring.errors import KeyringError, PasswordDeleteError

from app.core.errors import AppError
from app.models.connection import AuthType, ConnectionParams

log = logging.getLogger(__name__)

SERVICE_NAME = "ActuariaApp"
ENTRY_NAME = "sql_server_default"


class CredentialStore:
    """Guarda, recupera y elimina las credenciales recordadas."""

    def save(self, params: ConnectionParams) -> None:
        payload = json.dumps(
            {
                "server": params.server,
                "database": params.database,
                "auth_type": params.auth_type.value,
                "username": params.username,
                "password": params.password,
            }
        )
        print(payload)
        try:
            keyring.set_password(SERVICE_NAME, ENTRY_NAME, payload)
        except KeyringError:
            log.error("No se pudo escribir en el almacén de credenciales")
            raise AppError(
                "credential_store_error",
                "No se pudieron guardar las credenciales de forma segura.",
                500,
            ) from None

    def load(self) -> ConnectionParams | None:
        """Devuelve las credenciales guardadas o None si no existen o están dañadas."""
        try:
            raw = keyring.get_password(SERVICE_NAME, ENTRY_NAME)
        except KeyringError:
            log.error("No se pudo leer el almacén de credenciales")
            return None
        if not raw:
            return None
        try:
            data = json.loads(raw)
            return ConnectionParams(
                server=data["server"],
                database=data.get("database"),
                auth_type=AuthType(data["auth_type"]),
                username=data.get("username"),
                password=data.get("password"),
            )
        except (ValueError, KeyError):
            log.warning("Credenciales guardadas con formato inválido; se ignoran")
            return None

    def delete(self) -> None:
        """Elimina las credenciales. No falla si no había ninguna."""
        try:
            keyring.delete_password(SERVICE_NAME, ENTRY_NAME)
        except PasswordDeleteError:
            pass  # ya no existían
        except KeyringError:
            raise AppError(
                "credential_store_error",
                "No se pudieron eliminar las credenciales guardadas.",
                500,
            ) from None