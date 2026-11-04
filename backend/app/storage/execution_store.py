"""Persistencia local en SQLite de ejecuciones y resultados de extracción."""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

from app.models.extraction import (
    DATASETS,
    INVOICE_COLUMNS,
    RECORD_COLUMNS,
    TRANSACTION_COLUMNS,
    ExtractionStatus,
    ResultDataset,
)

log = logging.getLogger(__name__)

_JSON_FIELDS = frozenset({"parameters", "metrics", "warnings", "errors"})
_UPDATABLE = _JSON_FIELDS | {
    "status", "progress", "current_step", "started_at", "finished_at", "export_path",
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cols(columns: Sequence[str]) -> str:
    return ", ".join(f'"{c}" TEXT' for c in columns)


# Los identificadores provienen de constantes del código, nunca de entrada externa.
_DDL = f"""
CREATE TABLE IF NOT EXISTS executions (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    current_step TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    parameters TEXT NOT NULL DEFAULT '{{}}',
    metrics TEXT NOT NULL DEFAULT '{{}}',
    warnings TEXT NOT NULL DEFAULT '[]',
    errors TEXT NOT NULL DEFAULT '[]',
    export_path TEXT
);
CREATE TABLE IF NOT EXISTS extraction_records (
    execution_id TEXT NOT NULL, category TEXT NOT NULL, {_cols(RECORD_COLUMNS)}
);
CREATE INDEX IF NOT EXISTS ix_records ON extraction_records (execution_id, category);
CREATE TABLE IF NOT EXISTS extraction_invoices (
    execution_id TEXT NOT NULL, {_cols(INVOICE_COLUMNS)}
);
CREATE INDEX IF NOT EXISTS ix_invoices ON extraction_invoices (execution_id);
CREATE TABLE IF NOT EXISTS extraction_transactions (
    execution_id TEXT NOT NULL, {_cols(TRANSACTION_COLUMNS)}
);
CREATE INDEX IF NOT EXISTS ix_transactions ON extraction_transactions (execution_id);
"""


class ExecutionStore:
    """Acceso a SQLite. Una conexión por operación: seguro entre hilos."""

    def __init__(self, path: Path, retention_days: int = 30) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(_DDL)
        self.recover_interrupted()
        self.purge_older_than(retention_days)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---- Ejecuciones ------------------------------------------------------
    def create(self, execution_id: str, parameters: dict) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO executions (id, status, progress, created_at, parameters) "
                "VALUES (?, ?, 0, ?, ?)",
                (execution_id, ExtractionStatus.QUEUED.value, utcnow(),
                 json.dumps(parameters, default=str)),
            )

    def get(self, execution_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM executions WHERE id = ?", (execution_id,)).fetchone()
        if row is None:
            return None
        data = dict(row)
        for field in _JSON_FIELDS:
            data[field] = json.loads(data[field] or "null")
        data["status"] = ExtractionStatus(data["status"])
        return data

    def update(self, execution_id: str, **fields: Any) -> None:
        unknown = set(fields) - _UPDATABLE
        if unknown:
            raise ValueError(f"Campos no actualizables: {sorted(unknown)}")
        if not fields:
            return
        assignments, values = [], []
        for key, value in fields.items():
            if isinstance(value, ExtractionStatus):
                value = value.value
            elif key in _JSON_FIELDS:
                value = json.dumps(value, default=str)
            assignments.append(f"{key} = ?")
            values.append(value)
        with self._conn() as conn:
            conn.execute(
                f"UPDATE executions SET {', '.join(assignments)} WHERE id = ?",
                (*values, execution_id),
            )

    def recover_interrupted(self) -> None:
        """Ejecuciones que quedaron activas por un cierre de la app pasan a failed."""
        with self._conn() as conn:
            conn.execute(
                "UPDATE executions SET status = ?, finished_at = ?, errors = ? "
                "WHERE status IN (?, ?)",
                (ExtractionStatus.FAILED.value, utcnow(),
                 json.dumps(["La ejecución se interrumpió al cerrar la aplicación."]),
                 ExtractionStatus.QUEUED.value, ExtractionStatus.RUNNING.value),
            )

    def purge_older_than(self, days: int) -> None:
        """Retención: elimina resultados detallados (datos de salud) y archivos exportados."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, export_path FROM executions "
                "WHERE finished_at IS NOT NULL AND finished_at < ?", (cutoff,)
            ).fetchall()
            for row in rows:
                for table in ("extraction_records", "extraction_invoices", "extraction_transactions"):
                    conn.execute(f"DELETE FROM {table} WHERE execution_id = ?", (row["id"],))
                if row["export_path"]:
                    Path(row["export_path"]).unlink(missing_ok=True)
                    conn.execute("UPDATE executions SET export_path = NULL WHERE id = ?", (row["id"],))

    # ---- Resultados -------------------------------------------------------
    def insert_rows(self, dataset: ResultDataset, execution_id: str, rows: list[dict]) -> None:
        if not rows:
            return
        spec = DATASETS[dataset]
        cols = ("execution_id", *(("category",) if spec.category else ()), *spec.columns)
        sql = (
            f"INSERT INTO {spec.table} ({', '.join(f'\"{c}\"' for c in cols)}) "
            f"VALUES ({', '.join('?' * len(cols))})"
        )
        prefix = (execution_id, *((spec.category,) if spec.category else ()))
        data = [(*prefix, *(row.get(c) for c in spec.columns)) for row in rows]
        with self._conn() as conn:
            conn.executemany(sql, data)

    def delete_results(self, execution_id: str) -> None:
        with self._conn() as conn:
            for table in ("extraction_records", "extraction_invoices", "extraction_transactions"):
                conn.execute(f"DELETE FROM {table} WHERE execution_id = ?", (execution_id,))

    @staticmethod
    def _where(dataset: ResultDataset, execution_id: str, search: str | None) -> tuple[str, list]:
        spec = DATASETS[dataset]
        clauses, params = ["execution_id = ?"], [execution_id]
        if spec.category:
            clauses.append("category = ?")
            params.append(spec.category)
        if search and search.strip():
            escaped = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            ors = " OR ".join(f"\"{c}\" LIKE ? ESCAPE '\\'" for c in spec.columns)
            clauses.append(f"({ors})")
            params.extend([f"%{escaped}%"] * len(spec.columns))
        return " AND ".join(clauses), params

    def count(self, dataset: ResultDataset, execution_id: str, search: str | None = None) -> int:
        where, params = self._where(dataset, execution_id, search)
        with self._conn() as conn:
            return conn.execute(
                f"SELECT COUNT(*) FROM {DATASETS[dataset].table} WHERE {where}", params
            ).fetchone()[0]

    def page(
        self, dataset: ResultDataset, execution_id: str, page: int, page_size: int,
        search: str | None = None,
    ) -> tuple[list[dict], int]:
        spec = DATASETS[dataset]
        where, params = self._where(dataset, execution_id, search)
        cols = ", ".join(f'"{c}"' for c in spec.columns)
        with self._conn() as conn:
            total = conn.execute(f"SELECT COUNT(*) FROM {spec.table} WHERE {where}", params).fetchone()[0]
            rows = conn.execute(
                f"SELECT {cols} FROM {spec.table} WHERE {where} ORDER BY rowid LIMIT ? OFFSET ?",
                (*params, page_size, (page - 1) * page_size),
            ).fetchall()
        return [dict(r) for r in rows], total

    def iter_rows(
        self, dataset: ResultDataset, execution_id: str, batch_size: int = 5000
    ) -> Iterator[list[tuple]]:
        spec = DATASETS[dataset]
        where, params = self._where(dataset, execution_id, None)
        cols = ", ".join(f'"{c}"' for c in spec.columns)
        with self._conn() as conn:
            cursor = conn.execute(
                f"SELECT {cols} FROM {spec.table} WHERE {where} ORDER BY rowid", params
            )
            while batch := cursor.fetchmany(batch_size):
                yield [tuple(r) for r in batch]