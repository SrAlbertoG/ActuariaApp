from dataclasses import dataclass, field

from enum import Enum

class AuthType(str,Enum):
    SQL = "sql"
    WINDOWS = "windows"

@dataclass(frozen=True)
class ConnectionParams:

    server: str
    database: str | None
    auth_type: str | None = None
    username: str | None = None
    password: str | None = field(default=None, repr=False)