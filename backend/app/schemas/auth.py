"""Contratos de datos (request/response) del módulo de autenticación."""

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from app.models.connection import AuthType, ConnectionParams

# Rechaza ; { } para impedir inyección de parámetros en la cadena de conexión.
_SAFE = r"^[^;{}]+$"


class LoginRequest(BaseModel):
    """Datos que el analista ingresa en la pantalla de acceso."""

    model_config = ConfigDict(str_strip_whitespace=True)

    server: str = Field(min_length=1, max_length=255, pattern=_SAFE)
    database: str | None = Field(default=None, max_length=128, pattern=_SAFE)
    auth_type: AuthType = AuthType.SQL
    username: str | None = Field(default=None, max_length=128, pattern=_SAFE)
    # SecretStr: se oculta en repr, logs y mensajes de validación.
    password: SecretStr | None = None

    @model_validator(mode="after")
    def _sql_auth_needs_user_and_password(self) -> "LoginRequest":
        if self.auth_type == AuthType.SQL:
            if not self.username or not self.password:
                raise ValueError("Usuario y contraseña son obligatorios.")
        return self

    def to_params(self) -> ConnectionParams:
        return ConnectionParams(
            server=self.server,
            database=self.database or None,
            auth_type=self.auth_type,
            username=self.username,
            password=self.password.get_secret_value() if self.password else None,
        )


class SavedProfile(BaseModel):
    """Datos NO sensibles de las credenciales guardadas (sin contraseña)."""

    server: str
    database: str | None
    auth_type: AuthType
    username: str | None


class SessionStatus(BaseModel):
    """Estado de la conexión. Jamás incluye la contraseña."""

    connected: bool
    server: str | None = None
    database: str | None = None
    username: str | None = None
    auth_type: AuthType | None = None
    has_saved_credentials: bool = False
    saved_profile: SavedProfile | None = None

class WindowsInfo(BaseModel):
    """Cuenta de windows que se usuario con autentificacion integrada"""

    available : bool
    account : str | None = None
    domain_joined : bool = False
    message: str | None = None