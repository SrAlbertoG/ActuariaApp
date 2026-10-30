"""
Configuración central del backend.

Todos los valores se pueden sobrescribir con variables de entorno que
empiecen por ``ACTUARIA_`` (por ejemplo ``ACTUARIA_PORT=9000``). Tauri
usará este mecanismo para entregar al backend el puerto y el token de sesión.

IMPORTANTE (seguridad): aquí NO se guardan contraseñas de SQL Server.
Las credenciales viven únicamente en el almacén seguro de Windows.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """PARAMETROS DE EJECUCION DE LA APLICACION"""

    model_config = SettingsConfigDict(env_prefix="ACTUARIA_")

    #Nombre y version, utilies para logs y endpoint /health.

    app_name: str = "ActuariaApp"
    app_version: str = "0.1.0"

    #El backend solo escucha en Loopback (segun requisito de seguridad #1)
    #Se define como constante de configuracion y no se expone el usuario
    host: str = "127.0.0.1"
    port: int = 8765

    # Token compartido entre Tauri y FastAPI (requisito de seguridad #3).
    # En producción Tauri genera uno aleatorio por sesión; el valor por
    # defecto es SOLO para desarrollo.
    api_token: str = "dev-token-cambiar"

    # Directorio de trabajo: SQLite, temporales y exportaciones.
    data_dir: Path = Path.home() / "ActuariaApp"

    # Orígenes permitidos para CORS (Vite en desarrollo y Tauri en Windows).
    allowed_origins: list[str] = [
        "http://localhost:1420",
        "http://tauri.localhost",
        "tauri://localhost",
    ]

    #---SQL Server-----
    sql_driver: str = "OBDC Driver 17 for SQL Server"

    sql_login_timeout: int = 10

    sql_trust_server_certificate: bool = True

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