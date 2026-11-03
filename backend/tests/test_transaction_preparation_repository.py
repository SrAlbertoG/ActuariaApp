"""Pruebas de la validación de selección en SQL Server."""

from app.repositories.sql_server_transaction_repository import (
    SqlServerTransactionRepository,
)


class FakeCursor:
    description = [
        ("id",),
        ("invoice",),
        ("contract",),
        ("nit_provider",),
    ]

    def __init__(self, rows):
        self.rows = rows
        self.query = None
        self.params = None

    def execute(self, query, params):
        self.query = query
        self.params = params

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConnection:
    def __init__(self, rows):
        self.cursor_instance = FakeCursor(rows)

    def cursor(self):
        return self.cursor_instance


def test_validate_selection_checks_active_rows_by_invoice_and_transaction():
    connection = FakeConnection(
        [("501", "FE001", "CNT-2026-9", "900123456")]
    )
    repository = SqlServerTransactionRepository()

    result = repository.validate_selection(
        connection,
        [
            {
                "invoice": "FE001",
                "nit_provider": "900123456",
                "contract": "CNT-2026-9",
            }
        ],
        ["501"],
    )

    query = connection.cursor_instance.query
    params = connection.cursor_instance.params

    assert result[0]["id"] == "501"
    assert "rat_Activo = 'Activo'" in query
    assert "rat_NumeroFactura = ?" in query
    assert "rat_Id IN (?)" in query
    assert "rat_NumeroIdentificacion = ?" not in query
    assert params == ("FE001", "501")
