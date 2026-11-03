"""
Información sobre la cuenta de Windows con la que se ejecuta la aplicación.

La autenticación integrada de Windows NO usa credenciales guardadas: SQL Server
recibe la identidad de la sesión actual. Este módulo permite mostrar esa
identidad al usuario y avisar, ANTES de intentar conectar, cuando el equipo
no está unido a un dominio (en ese caso es muy probable que un servidor
externo rechace la cuenta).
"""

import getpass
import os
import sys
from typing import Mapping


def get_windows_identity(
    env: Mapping[str, str] | None = None, platform: str | None = None
) -> dict:
    """
    Devuelve ``available``, ``account``, ``domain_joined`` y ``message``.

    Los parámetros ``env`` y ``platform`` existen para poder probar la lógica
    sin depender del equipo donde corre la prueba.

    Heurística de dominio: en una cuenta local, USERDOMAIN coincide con el
    nombre del equipo (COMPUTERNAME); en una cuenta de dominio es distinto.
    """
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform

    if platform != "win32":
        return {
            "available": False,
            "account": None,
            "domain_joined": False,
            "message": "La autenticación de Windows solo está disponible en Windows.",
        }

    user = env.get("USERNAME") or getpass.getuser()
    domain = env.get("USERDOMAIN", "")
    computer = env.get("COMPUTERNAME", "")
    account = f"{domain}\\{user}" if domain else user
    domain_joined = bool(domain) and domain.upper() != computer.upper()

    message = None
    if not domain_joined:
        message = (
            "Este equipo no parece estar unido a un dominio, por lo que es "
            "probable que el servidor no reconozca tu cuenta de Windows. "
            "Si el intento falla, usa usuario y contraseña de SQL Server."
        )
    return {
        "available": True,
        "account": account,
        "domain_joined": domain_joined,
        "message": message,
    }