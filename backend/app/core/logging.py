"""
Configuración de logging con enmascaramiento de datos sensibles.

Requisito de seguridad: no registrar contraseñas ni cadenas de conexión
completas. Se aplica un filtro a TODOS los mensajes que pasan por el logger,
de modo que aunque alguien escriba ``log.info(conn_str)`` por error, el
secreto no llega al archivo.
"""

import logging
import re
from logging.handlers import RotatingFileHandler

from app.core.config import get_settings

# Detecta pares clave=valor sensibles: PWD=..., password: ..., contraseña=...
_SENSITIVE = re.compile(
    r"(?i)\b(pwd|password|passwd|contraseña|contrasena|token)\b(\s*[=:]\s*)([^;,\s]+)"
)


class RedactingFilter(logging.Filter):
    """Reemplaza valores sensibles por ``***`` antes de escribir el log."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()  # ya con los argumentos interpolados
        record.msg = _SENSITIVE.sub(r"\1\2***", message)
        record.args = ()  # evita que se vuelva a formatear
        return True


def setup_logging() -> None:
    """Configura el logger raíz con salida a consola y archivo rotativo."""
    settings = get_settings()
    settings.ensure_directories()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    redactor = RedactingFilter()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.addFilter(redactor)

    file_handler = RotatingFileHandler(
        settings.logs_dir / "backend.log",
        maxBytes=5_000_000,  # 5 MB por archivo
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(redactor)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()  # evita duplicados si se llama dos veces
    root.addHandler(console)
    root.addHandler(file_handler)