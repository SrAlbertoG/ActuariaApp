"""
Configuración central del backend.

Todos los valores se pueden sobrescribir con variables de entorno que
empiecen por ACTUARIA_. Las rutas de los archivos de entrada son configurables
para que cada instalación local pueda utilizar una ubicación distinta.
"""

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# La raíz se resuelve desde el código y no desde el directorio de trabajo
# actual, que puede variar al ejecutar FastAPI desde Tauri o PyInstaller.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Parámetros de ejecución de la aplicación."""

    model_config = SettingsConfigDict(env_prefix="ACTUARIA_")

    app_name: str = "ActuariaApp"
    app_version: str = "0.1.0"

    # El backend solo escucha en loopback.
    host: str = "127.0.0.1"
    port: int = 8765

    # Token compartido entre Tauri y FastAPI. El valor por defecto es solo
    # para desarrollo; Tauri debe generar uno aleatorio en producción.
    api_token: str = "dev-token-cambiar"

    # Directorio local de metadatos, temporales y exportaciones.
    data_dir: Path = Path.home() / "ActuariaApp"

    allowed_origins: list[str] = [
        "http://localhost:1420",
        "http://tauri.localhost",
        "tauri://localhost",
    ]

    # Configuración SQL Server.
    sql_driver: str = "ODBC Driver 17 for SQL Server"
    sql_login_timeout: int = 10
    sql_trust_server_certificate: bool = True

    # Configuración de fuentes de facturación.
    # Por defecto, el Excel se espera dentro de resources/inputs.
    # Se puede cambiar sin modificar código con ACTUARIA_FIXED_COSTS_FILE.
    fixed_costs_file: Path = (
        PROJECT_ROOT / "resources" / "inputs" / "BaseMontosFijos2026.xlsx"
    )
    invoice_source_cutoff: date = date(2026, 9, 1)

    # En FPR se filtra por FechaFactura por defecto. El área puede cambiarlo
    # a FechaRadicacion mediante ACTUARIA_FPR_PERIOD_FIELD.
    fpr_period_field: Literal["FechaFactura", "FechaRadicacion"] = "FechaFactura"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def temp_dir(self) -> Path:
        return self.data_dir / "temp"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"

    def ensure_directories(self) -> None:
        """Crea los directorios de trabajo si no existen."""
        for folder in (self.data_dir, self.logs_dir, self.temp_dir, self.exports_dir):
            folder.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Devuelve una única instancia de Settings (patrón singleton)."""
    return Settings()
