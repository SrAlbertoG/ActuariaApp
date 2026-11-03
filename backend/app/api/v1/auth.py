"""Endpoints de autenticación contra SQL Server (/api/v1/auth/sql-server)."""

from fastapi import APIRouter, Depends

from app.schemas.auth import LoginRequest, SessionStatus
from app.services.auth_service import AuthService, get_auth_service

from app.core.windows_identity import get_windows_identity
from app.schemas.auth import LoginRequest, SessionStatus, WindowsInfo

router = APIRouter(prefix="/auth/sql-server", tags=["autenticación"])


@router.post("/login", response_model=SessionStatus)
def login(body: LoginRequest, svc: AuthService = Depends(get_auth_service)):
    """Valida las credenciales con una conexión real y abre la sesión."""
    svc.login(body.to_params())
    return svc.status()


@router.get("/status", response_model=SessionStatus)
def status(svc: AuthService = Depends(get_auth_service)):
    """Estado de la conexión y datos no sensibles de las credenciales guardadas."""
    return svc.status()


@router.post("/auto-login", response_model=SessionStatus)
def auto_login(svc: AuthService = Depends(get_auth_service)):
    """Intenta reconectar con las credenciales guardadas (se llama al iniciar)."""
    svc.auto_login()
    return svc.status()


@router.post("/remember", response_model=SessionStatus)
def remember(svc: AuthService = Depends(get_auth_service)):
    """Guarda de forma segura las credenciales de la sesión activa."""
    svc.remember()
    return svc.status()


@router.delete("/credentials", response_model=SessionStatus)
def delete_credentials(svc: AuthService = Depends(get_auth_service)):
    """Elimina las credenciales guardadas del almacén seguro."""
    svc.forget_credentials()
    return svc.status()


@router.post("/logout", response_model=SessionStatus)
def logout(svc: AuthService = Depends(get_auth_service)):
    """Cierra la sesión actual."""
    svc.logout()
    return svc.status()

@router.get("/windows-info", response_model=WindowsInfo)
def windows_info():
    """Cuenta de Windows que se usaria y si el equipo parece estar en un dominio"""
    
    return get_windows_identity()