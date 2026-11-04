"""Singletons y dependencias de la extracción."""

from functools import lru_cache

from fastapi import Depends

from app.api.deps import require_sql_connection
from app.core.config import get_settings
from app.core.task_manager import LocalTaskManager
from app.services.auth_service import AuthService
from app.services.export_service import ExportService
from app.services.extraction_service import ExtractionQueryService, ExtractionService
from app.storage.execution_store import ExecutionStore


@lru_cache
def get_store() -> ExecutionStore:
    settings = get_settings()
    settings.ensure_directories()
    return ExecutionStore(settings.database_path, settings.results_retention_days)


@lru_cache
def get_task_manager() -> LocalTaskManager:
    return LocalTaskManager(max_workers=2)


def get_extraction_service(
    auth_service: AuthService = Depends(require_sql_connection),
) -> ExtractionService:
    return ExtractionService(auth_service, get_store(), get_task_manager())


def get_query_service() -> ExtractionQueryService:
    return ExtractionQueryService(get_store(), get_task_manager())


def get_export_service() -> ExportService:
    return ExportService(get_store(), get_settings().exports_dir)