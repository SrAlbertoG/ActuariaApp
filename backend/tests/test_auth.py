import logging

import pytest 
import pyodbc
from fastapi.testclient import TestClient
from app.core.windows_identity import get_windows_identity
from app.models.connection import AuthType
from app.core import credential_store
from app.core.config import get_settings
from app.core.errors import AppError
from app.integrations.sql_server import connection as sql
from app.main import app
from app.services.auth_service import AuthService, get_auth_service

def _driver_error(state: str, text: str) -> pyodbc.Error:
    return pyodbc.Error(state, text)

LOGIN_FAILED = (
    "[28000] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]"
    "Login failed for user 'X'. (18456) (SQLDriverConnect)"
)

PASSWORD = "S3cr3t!;}" #Incluye caracteres problematicos }; aproposito
BODY = {
    "server" : "servidor-prueba",
    "database" : "BaseDemo",
    "auth_type" : "sql",
    "username" : "analista",
    "password" : PASSWORD,
}
HEADERS = {"X-Session-Token" : get_settings().api_token}

class FakeKeyring:
    """Reemplaza el Administrador de credenciales de Windows Memoria"""

    def __init__(self):
        self.data = {}
    def set_password(self,service,user,value):
        self.data[(service,user)] = value
    def get_password(self,service,user):
        return self.data.get((service,user))
    def delete_password(self,service,user):
        if (service,user) not in self.data:
            raise credential_store.PasswordDeleteError()
        del self.data[(service,user)]

class FakeConn:
    def close(self):
        pass

@pytest.fixture
def fake_keyring(monkeypatch):
    fake = FakeKeyring()
    monkeypatch.setattr(credential_store,"keyring",fake)
    return fake

@pytest.fixture
def client(fake_keyring,monkeypatch):
    """Cliente con servicio limpio y conexion a SQL Server simulada (existosa)."""
    monkeypatch.setattr(sql,"open_connection",lambda params: FakeConn())
    service = AuthService()
    app.dependency_overrides[get_auth_service] = lambda : service
    yield TestClient(app)
    app.dependency_overrides.clear()

def url(path: str) -> str:
    return f"/api/v1/auth/sql-server/{path}"

def test_login_exitoso_y_sin_contrasena_en_respuesta(client):
    r = client.post(url("login"), json=BODY, headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["connected"] is True
    assert data["server"] == "servidor-prueba"
    assert PASSWORD not in r.text


def test_credenciales_incorrectas(client, monkeypatch):
    def fail(_):
        raise AppError("invalid_credentials", "Usuario o contraseña incorrectos.", 401)

    monkeypatch.setattr(sql, "open_connection", fail)
    r = client.post(url("login"), json=BODY, headers=HEADERS)
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_credentials"
    assert client.get(url("status"), headers=HEADERS).json()["connected"] is False


def test_sql_auth_exige_usuario_y_contrasena(client):
    r = client.post(url("login"), json={"server": "x", "auth_type": "sql"}, headers=HEADERS)
    assert r.status_code == 422


def test_rechaza_inyeccion_en_cadena_de_conexion(client):
    body = {**BODY, "server": "srv;Trusted_Connection=yes"}
    assert client.post(url("login"), json=body, headers=HEADERS).status_code == 422


def test_recordar_exige_sesion_activa(client):
    r = client.post(url("remember"), headers=HEADERS)
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "not_connected"


def test_recordar_y_reconexion_automatica_tras_reinicio(client, fake_keyring):
    client.post(url("login"), json=BODY, headers=HEADERS)
    assert client.post(url("remember"), headers=HEADERS).json()["has_saved_credentials"]

    # Simula reiniciar la aplicación: servicio nuevo, mismo almacén seguro.
    app.dependency_overrides[get_auth_service] = lambda: AuthService()
    assert client.get(url("status"), headers=HEADERS).json()["connected"] is False

    r = client.post(url("auto-login"), headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["connected"] is True


def test_auto_login_sin_credenciales_no_falla(client):
    r = client.post(url("auto-login"), headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["connected"] is False


def test_auto_login_fallido_conserva_credenciales(client, monkeypatch):
    client.post(url("login"), json=BODY, headers=HEADERS)
    client.post(url("remember"), headers=HEADERS)
    app.dependency_overrides[get_auth_service] = lambda: AuthService()

    def fail(_):
        raise AppError("server_unavailable", "Sin servidor.", 503)

    monkeypatch.setattr(sql, "open_connection", fail)
    assert client.post(url("auto-login"), headers=HEADERS).status_code == 503
    assert client.get(url("status"), headers=HEADERS).json()["has_saved_credentials"]


def test_eliminar_credenciales(client, fake_keyring):
    client.post(url("login"), json=BODY, headers=HEADERS)
    client.post(url("remember"), headers=HEADERS)
    r = client.delete(url("credentials"), headers=HEADERS)
    assert r.json()["has_saved_credentials"] is False
    assert fake_keyring.data == {}


def test_logout(client):
    client.post(url("login"), json=BODY, headers=HEADERS)
    assert client.post(url("logout"), headers=HEADERS).json()["connected"] is False


def test_contrasena_no_aparece_en_logs(client, caplog):
    with caplog.at_level(logging.DEBUG):
        client.post(url("login"), json=BODY, headers=HEADERS)
        client.post(url("remember"), headers=HEADERS)
    assert PASSWORD not in caplog.text


def test_cadena_de_conexion_escapa_la_contrasena():
    from app.models.connection import AuthType, ConnectionParams

    params = ConnectionParams("srv", "db", AuthType.SQL, "usr", "a;b}c")
    cs = sql.build_connection_string(params, "ODBC Driver 17 for SQL Server")
    assert "PWD={a;b}}c};" in cs

def test_rechazo_con_sql_dice_usuario_o_contrasena():
    err = sql.classify_error(_driver_error("28000", LOGIN_FAILED), AuthType.SQL)
    assert err.code == "invalid_credentials"


def test_rechazo_con_windows_no_dice_usuario_o_contrasena():
    err = sql.classify_error(_driver_error("28000", LOGIN_FAILED), AuthType.WINDOWS)
    assert err.code == "windows_auth_failed"


def test_windows_dominio_no_confiable_y_sspi():
    untrusted = "[28000] ...Login failed. The login is from an untrusted domain. (18452)"
    sspi = "[HY000] ...Cannot generate SSPI context"
    for text in (untrusted, sspi):
        err = sql.classify_error(_driver_error("28000", text), AuthType.WINDOWS)
        assert err.code == "windows_auth_failed"


def test_windows_sin_driver_o_sin_servidor_no_se_confunde():
    assert sql.classify_error(_driver_error("IM002", "x"), AuthType.WINDOWS).code == "driver_missing"
    timeout = "[HYT00] Login timeout expired (0) (SQLDriverConnect)"
    assert sql.classify_error(_driver_error("HYT00", timeout), AuthType.WINDOWS).code == "server_unavailable"


def test_identidad_windows_equipo_con_dominio():
    env = {"USERNAME": "analista", "USERDOMAIN": "COMFENALCO", "COMPUTERNAME": "PC-01"}
    info = get_windows_identity(env, "win32")
    assert info["domain_joined"] is True
    assert info["account"] == "COMFENALCO\\analista"
    assert info["message"] is None


def test_identidad_windows_equipo_local_avisa():
    env = {"USERNAME": "analista", "USERDOMAIN": "PC-01", "COMPUTERNAME": "PC-01"}
    info = get_windows_identity(env, "win32")
    assert info["domain_joined"] is False
    assert info["message"]


def test_endpoint_windows_info(client):
    r = client.get(url("windows-info"), headers=HEADERS)
    assert r.status_code == 200
    assert {"available", "account", "domain_joined"} <= set(r.json())
