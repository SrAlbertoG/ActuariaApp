import { useMemo, useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { extractionApi, PAGE_SIZE } from "./extractionApi";
import type {
  Invoice,
  InvoiceFilters,
  PreparedSelection,
  Transaction,
} from "./types";

const EMPTY_FILTERS: InvoiceFilters = {
  contract: "",
  provider_nit: "",
  invoice: "",
  start_date: "",
  end_date: "",
};

const MAX_SELECTED_INVOICES = 250;

const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-slate-100";
const labelClass =
  "mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500";

function formatCurrency(value: string | number | null): string {
  if (value === null || value === "") return "—";
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "—";

  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value.slice(0, 10) + "T00:00:00");

  return Number.isNaN(parsed.getTime())
    ? value
    : new Intl.DateTimeFormat("es-CO").format(parsed);
}

function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (nextPage: number) => void;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const firstRow = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const lastRow = Math.min(page * pageSize, total);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-4 py-3">
      <p className="text-xs text-slate-500">
        {firstRow}–{lastRow} de {total.toLocaleString("es-CO")} registros
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Anterior
        </button>
        <span className="min-w-20 text-center text-xs text-slate-600">
          Página {page} de {totalPages}
        </span>
        <button
          type="button"
          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Siguiente
        </button>
      </div>
    </div>
  );
}

function SourcePill({ source }: { source: Invoice["source"] }) {
  const isSql = source === "sql_server";

  return (
    <span
      className={
        "inline-flex rounded-full px-2 py-1 text-[11px] font-semibold " +
        (isSql ? "bg-blue-50 text-blue-700" : "bg-violet-50 text-violet-700")
      }
    >
      {isSql ? "SQL Server" : "Montos fijos"}
    </span>
  );
}

/** Muestra la información ampliada de la factura desde el endpoint de detalle. */
function InvoiceDetail({
  invoiceId,
  onClose,
}: {
  invoiceId: string;
  onClose: () => void;
}) {
  const detail = useQuery({
    queryKey: ["invoice-detail", invoiceId],
    queryFn: () => extractionApi.getInvoice(invoiceId),
  });

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        aria-labelledby="invoice-detail-title"
        aria-modal="true"
        className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl"
        role="dialog"
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-blue-600">
              Facturación
            </p>
            <h2
              id="invoice-detail-title"
              className="mt-1 text-xl font-semibold text-slate-900"
            >
              Detalle de factura
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-2 py-1 text-slate-500 hover:bg-slate-100"
            aria-label="Cerrar detalle"
          >
            ×
          </button>
        </div>

        {detail.isPending ? (
          <p className="py-8 text-sm text-slate-500">Consultando factura…</p>
        ) : detail.isError ? (
          <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {detail.error.message}
          </p>
        ) : (
          <>
            <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <DetailField label="Factura" value={detail.data.invoice} />
              <DetailField label="Contrato" value={detail.data.contract} />
              <DetailField label="NIT prestador" value={detail.data.nit_provider} />
              <DetailField
                label="Prestador"
                value={detail.data.provider_name ?? "No disponible"}
              />
              <DetailField
                label="Mes de servicio"
                value={detail.data.service_month ?? "No disponible"}
              />
              <DetailField
                label="Fecha factura"
                value={formatDate(detail.data.invoice_date)}
              />
              <DetailField
                label="Fecha radicación"
                value={formatDate(detail.data.filing_date)}
              />
              <DetailField
                label="Valor radicado"
                value={formatCurrency(detail.data.billed_amount)}
              />
            </dl>
            <div className="mt-5">
              <SourcePill source={detail.data.source} />
            </div>
          </>
        )}
      </section>
    </div>
  );
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="mt-1 break-words text-sm font-semibold text-slate-800">
        {value}
      </dd>
    </div>
  );
}

/** Pantalla principal del entregable 2: búsqueda, revisión y selección. */
export function GenerationPage() {
  const [filters, setFilters] = useState<InvoiceFilters>(EMPTY_FILTERS);
  const [appliedFilters, setAppliedFilters] =
    useState<InvoiceFilters>(EMPTY_FILTERS);
  const [hasSearched, setHasSearched] = useState(false);
  const [filterError, setFilterError] = useState<string | null>(null);
  const [invoicePage, setInvoicePage] = useState(1);
  const [transactionPage, setTransactionPage] = useState(1);
  const [selectedInvoices, setSelectedInvoices] = useState<
    Record<string, Invoice>
  >({});
  const [selectedTransactions, setSelectedTransactions] = useState<
    Record<string, Transaction>
  >({});
  const [detailInvoiceId, setDetailInvoiceId] = useState<string | null>(null);
  const [prepared, setPrepared] = useState<PreparedSelection | null>(null);

  const contracts = useQuery({
    queryKey: ["invoice-contracts"],
    queryFn: () => extractionApi.getContracts(),
  });

  const invoices = useQuery({
    queryKey: ["invoices", appliedFilters, invoicePage],
    queryFn: () => extractionApi.searchInvoices(appliedFilters, invoicePage),
    enabled: hasSearched,
  });

  const selectedInvoiceIds = useMemo(
    () => Object.keys(selectedInvoices).sort(),
    [selectedInvoices],
  );

  const transactions = useQuery({
    queryKey: ["transactions", selectedInvoiceIds, transactionPage],
    queryFn: () =>
      extractionApi.searchTransactions(selectedInvoiceIds, transactionPage),
    enabled: selectedInvoiceIds.length > 0,
  });

  const invoiceRows = invoices.data?.items ?? [];
  const transactionRows = transactions.data?.items ?? [];

  const allVisibleInvoicesSelected =
    invoiceRows.length > 0 &&
    invoiceRows.every((invoice) => Boolean(selectedInvoices[invoice.id]));

  const allVisibleTransactionsSelected =
    transactionRows.length > 0 &&
    transactionRows.every((transaction) =>
      Boolean(selectedTransactions[transaction.id]),
    );

  const selectedInvoiceCount = selectedInvoiceIds.length;
  const selectedTransactionIds = Object.keys(selectedTransactions);

  const handleFilterChange = (
    field: keyof InvoiceFilters,
    value: string,
  ) => {
    setFilters((current) => ({
      ...current,
      [field]: value,
      ...(field === "contract" ? { provider_nit: "" } : {}),
    }));
    setFilterError(null);
  };

  const handleSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (
      filters.start_date &&
      filters.end_date &&
      filters.start_date > filters.end_date
    ) {
      setFilterError(
        "La fecha inicial no puede ser posterior a la fecha final.",
      );
      return;
    }

    setAppliedFilters({ ...filters });
    setInvoicePage(1);
    setTransactionPage(1);
    setSelectedInvoices({});
    setSelectedTransactions({});
    setPrepared(null);
    setHasSearched(true);
    setFilterError(null);
  };

  const handleClear = () => {
    setFilters(EMPTY_FILTERS);
    setAppliedFilters(EMPTY_FILTERS);
    setInvoicePage(1);
    setTransactionPage(1);
    setSelectedInvoices({});
    setSelectedTransactions({});
    setPrepared(null);
    setHasSearched(false);
    setFilterError(null);
  };

  const toggleInvoice = (invoice: Invoice, checked: boolean) => {
    setSelectedInvoices((current) => {
      const next = { ...current };

      if (checked) {
        if (Object.keys(next).length < MAX_SELECTED_INVOICES) {
          next[invoice.id] = invoice;
        }
      } else {
        delete next[invoice.id];
      }

      return next;
    });

    if (!checked) {
      setSelectedTransactions((current) => {
        const next = { ...current };
        Object.keys(next).forEach((id) => {
          if (
            next[id].invoice === invoice.invoice &&
            next[id].nit_provider === invoice.nit_provider &&
            next[id].contract === invoice.contract
          ) {
            delete next[id];
          }
        });
        return next;
      });
    }

    setTransactionPage(1);
    setPrepared(null);
  };

  const toggleVisibleInvoices = (checked: boolean) => {
    setSelectedInvoices((current) => {
      const next = { ...current };

      if (checked) {
        for (const invoice of invoiceRows) {
          if (
            Object.keys(next).length >= MAX_SELECTED_INVOICES &&
            !next[invoice.id]
          ) {
            break;
          }
          next[invoice.id] = invoice;
        }
      } else {
        invoiceRows.forEach((invoice) => delete next[invoice.id]);
      }

      return next;
    });

    if (!checked) {
      setSelectedTransactions((current) => {
        const next = { ...current };
        const removed = new Set(
          invoiceRows.map((invoice) =>
            [invoice.invoice, invoice.nit_provider, invoice.contract].join("|"),
          ),
        );
        Object.keys(next).forEach((id) => {
          const transaction = next[id];
          const key = [
            transaction.invoice,
            transaction.nit_provider,
            transaction.contract,
          ].join("|");
          if (removed.has(key)) delete next[id];
        });
        return next;
      });
    }

    setTransactionPage(1);
    setPrepared(null);
  };

  const toggleTransaction = (
    transaction: Transaction,
    checked: boolean,
  ) => {
    setSelectedTransactions((current) => {
      const next = { ...current };
      if (checked) next[transaction.id] = transaction;
      else delete next[transaction.id];
      return next;
    });
    setPrepared(null);
  };

  const toggleVisibleTransactions = (checked: boolean) => {
    setSelectedTransactions((current) => {
      const next = { ...current };
      transactionRows.forEach((transaction) => {
        if (checked) next[transaction.id] = transaction;
        else delete next[transaction.id];
      });
      return next;
    });
    setPrepared(null);
  };

  const handlePrepare = () => {
    if (selectedInvoiceCount === 0 || selectedTransactionIds.length === 0) {
      return;
    }

    // El entregable 2 solo prepara la selección; la extracción pertenece
    // al entregable 3 y no se ejecuta desde este botón.
    setPrepared({
      invoiceIds: selectedInvoiceIds,
      transactionIds: selectedTransactionIds,
      preparedAt: new Date().toISOString(),
    });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center justify-between gap-3 px-6 py-4">
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
            >
              ← Inicio
            </Link>
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-blue-600">
                Plataforma de Actuaría
              </p>
              <h1 className="text-lg font-semibold text-slate-900">
                Generación de RIPS
              </h1>
            </div>
          </div>
          <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
            Conexión SQL activa
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-[1500px] space-y-5 px-6 py-6">
        <section>
          <div className="mb-4">
            <h2 className="text-base font-semibold text-slate-900">
              Parámetros de búsqueda
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Filtra las facturas y selecciona las transacciones que participarán
              en la extracción.
            </p>
          </div>

          <form
            onSubmit={handleSearch}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
              <div>
                <label className={labelClass} htmlFor="contract">
                  Contrato
                </label>
                <select
                  id="contract"
                  className={inputClass}
                  value={filters.contract}
                  onChange={(event) =>
                    handleFilterChange("contract", event.target.value)
                  }
                >
                  <option value="">Todos los contratos</option>
                  {contracts.data?.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
                {contracts.isError && (
                  <p className="mt-1 text-xs text-red-600">
                    No fue posible cargar contratos.
                  </p>
                )}
              </div>

              <div>
                <label className={labelClass} htmlFor="provider">
                  NIT del prestador
                </label>
                <input
                  id="provider"
                  inputMode="numeric"
                  className={inputClass}
                  placeholder="Ej. 900123456"
                  value={filters.provider_nit}
                  onChange={(event) =>
                    handleFilterChange("provider_nit", event.target.value)
                  }
                />
              </div>

              <div>
                <label className={labelClass} htmlFor="start-date">
                  Periodo desde
                </label>
                <input
                  id="start-date"
                  type="date"
                  className={inputClass}
                  value={filters.start_date}
                  onChange={(event) =>
                    handleFilterChange("start_date", event.target.value)
                  }
                />
              </div>

              <div>
                <label className={labelClass} htmlFor="end-date">
                  Periodo hasta
                </label>
                <input
                  id="end-date"
                  type="date"
                  className={inputClass}
                  value={filters.end_date}
                  min={filters.start_date || undefined}
                  onChange={(event) =>
                    handleFilterChange("end_date", event.target.value)
                  }
                />
              </div>

              <div>
                <label className={labelClass} htmlFor="invoice-filter">
                  Número de factura
                </label>
                <input
                  id="invoice-filter"
                  className={inputClass}
                  placeholder="Ej. FE12345"
                  value={filters.invoice}
                  onChange={(event) =>
                    handleFilterChange("invoice", event.target.value)
                  }
                />
              </div>
            </div>

            {filterError && (
              <p role="alert" className="mt-4 text-sm text-red-700">
                {filterError}
              </p>
            )}

            <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
              <p className="max-w-3xl text-xs text-slate-500">
                Fuentes: Base Montos Fijos hasta agosto de 2026 y SQL Server
                desde septiembre de 2026. El filtro de fecha FPR se configura
                en el backend.
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
                  onClick={handleClear}
                >
                  Limpiar
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700"
                >
                  Buscar facturas
                </button>
              </div>
            </div>
          </form>
        </section>

        {invoices.data?.warnings.map((warning) => (
          <div
            key={warning}
            role="status"
            className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
          >
            {warning}
          </div>
        ))}

        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
            <div>
              <h2 className="font-semibold text-slate-900">
                Facturas encontradas
              </h2>
              <p className="mt-0.5 text-xs text-slate-500">
                Selecciona una o varias facturas para consultar sus transacciones.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                {selectedInvoiceCount} seleccionadas
              </span>
              <span className="text-xs text-slate-500">
                {invoices.data?.total.toLocaleString("es-CO") ?? "—"} resultados
              </span>
            </div>
          </div>

          {!hasSearched ? (
            <p className="px-5 py-12 text-center text-sm text-slate-500">
              Define los filtros y pulsa “Buscar facturas” para consultar la
              información disponible.
            </p>
          ) : invoices.isPending ? (
            <p className="px-5 py-12 text-center text-sm text-slate-500">
              Consultando facturas…
            </p>
          ) : invoices.isError ? (
            <p
              role="alert"
              className="m-5 rounded-lg bg-red-50 p-4 text-sm text-red-700"
            >
              {invoices.error.message}
            </p>
          ) : invoiceRows.length === 0 ? (
            <p className="px-5 py-12 text-center text-sm text-slate-500">
              No se encontraron facturas con los filtros seleccionados.
            </p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[1050px] text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="w-12 px-4 py-3">
                        <input
                          type="checkbox"
                          aria-label="Seleccionar facturas visibles"
                          checked={allVisibleInvoicesSelected}
                          onChange={(event) =>
                            toggleVisibleInvoices(event.target.checked)
                          }
                        />
                      </th>
                      <th className="px-4 py-3">Factura</th>
                      <th className="px-4 py-3">NIT / Prestador</th>
                      <th className="px-4 py-3">Contrato</th>
                      <th className="px-4 py-3">Mes de servicio</th>
                      <th className="px-4 py-3 text-right">Valor radicado</th>
                      <th className="px-4 py-3">Fuente</th>
                      <th className="px-4 py-3 text-right">Detalle</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {invoiceRows.map((invoice) => (
                      <tr key={invoice.id} className="hover:bg-slate-50/80">
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            aria-label={"Seleccionar factura " + invoice.invoice}
                            checked={Boolean(selectedInvoices[invoice.id])}
                            disabled={
                              selectedInvoiceCount >= MAX_SELECTED_INVOICES &&
                              !selectedInvoices[invoice.id]
                            }
                            onChange={(event) =>
                              toggleInvoice(invoice, event.target.checked)
                            }
                          />
                        </td>
                        <td className="px-4 py-3 font-semibold text-slate-800">
                          {invoice.invoice}
                        </td>
                        <td className="px-4 py-3">
                          <p className="font-medium text-slate-700">
                            {invoice.nit_provider}
                          </p>
                          <p className="text-xs text-slate-500">
                            {invoice.provider_name ?? "Nombre no disponible"}
                          </p>
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {invoice.contract}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {invoice.service_month ?? "—"}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                          {formatCurrency(invoice.billed_amount)}
                        </td>
                        <td className="px-4 py-3">
                          <SourcePill source={invoice.source} />
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            type="button"
                            onClick={() => setDetailInvoiceId(invoice.id)}
                            className="font-medium text-blue-700 hover:text-blue-900"
                          >
                            Ver detalle
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination
                page={invoicePage}
                pageSize={PAGE_SIZE}
                total={invoices.data.total}
                onPageChange={setInvoicePage}
              />
              {selectedInvoiceCount >= MAX_SELECTED_INVOICES && (
                <p className="px-5 pb-3 text-xs text-amber-700">
                  Has alcanzado el máximo de {MAX_SELECTED_INVOICES} facturas
                  por consulta de transacciones.
                </p>
              )}
            </>
          )}
        </section>

        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
            <div>
              <h2 className="font-semibold text-slate-900">
                Transacciones RIPS
              </h2>
              <p className="mt-0.5 text-xs text-slate-500">
                Registros activos asociados a las facturas seleccionadas.
              </p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
              {selectedTransactionIds.length} transacciones seleccionadas
            </span>
          </div>

          {selectedInvoiceCount === 0 ? (
            <p className="px-5 py-12 text-center text-sm text-slate-500">
              Selecciona facturas en la tabla anterior para consultar sus
              transacciones.
            </p>
          ) : transactions.isPending ? (
            <p className="px-5 py-12 text-center text-sm text-slate-500">
              Consultando transacciones activas…
            </p>
          ) : transactions.isError ? (
            <p
              role="alert"
              className="m-5 rounded-lg bg-red-50 p-4 text-sm text-red-700"
            >
              {transactions.error.message}
            </p>
          ) : transactionRows.length === 0 ? (
            <p className="px-5 py-12 text-center text-sm text-slate-500">
              Las facturas seleccionadas no tienen transacciones RIPS activas.
            </p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[950px] text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="w-12 px-4 py-3">
                        <input
                          type="checkbox"
                          aria-label="Seleccionar transacciones visibles"
                          checked={allVisibleTransactionsSelected}
                          onChange={(event) =>
                            toggleVisibleTransactions(event.target.checked)
                          }
                        />
                      </th>
                      <th className="px-4 py-3">Código transacción</th>
                      <th className="px-4 py-3">Factura</th>
                      <th className="px-4 py-3">Contrato</th>
                      <th className="px-4 py-3">NIT prestador</th>
                      <th className="px-4 py-3">Código prestador</th>
                      <th className="px-4 py-3">Fecha RIPS</th>
                      <th className="px-4 py-3">Fecha radicación</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {transactionRows.map((transaction: Transaction) => (
                      <tr key={transaction.id} className="hover:bg-slate-50/80">
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            aria-label={
                              "Seleccionar transacción " + transaction.id
                            }
                            checked={Boolean(
                              selectedTransactions[transaction.id],
                            )}
                            onChange={(event) =>
                              toggleTransaction(
                                transaction,
                                event.target.checked,
                              )
                            }
                          />
                        </td>
                        <td className="px-4 py-3 font-semibold text-slate-800">
                          {transaction.id}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {transaction.invoice}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {transaction.contract}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {transaction.nit_provider}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {transaction.provider_code ?? "—"}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {formatDate(transaction.rips_date)}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {formatDate(transaction.filing_date)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination
                page={transactionPage}
                pageSize={PAGE_SIZE}
                total={transactions.data.total}
                onPageChange={setTransactionPage}
              />
            </>
          )}
        </section>

        <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-blue-100 bg-blue-50/60 p-5">
          <div>
            <h2 className="font-semibold text-slate-900">
              Preparar selección
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Confirma las facturas y transacciones que pasarán al proceso de
              extracción del entregable 3.
            </p>
          </div>
          <button
            type="button"
            onClick={handlePrepare}
            disabled={
              selectedInvoiceCount === 0 || selectedTransactionIds.length === 0
            }
            className="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Confirmar selección
          </button>
        </section>

        {prepared && (
          <section
            role="status"
            className="rounded-2xl border border-emerald-200 bg-white p-5 shadow-sm"
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-emerald-700">
              Selección preparada
            </p>
            <h2 className="mt-1 text-lg font-semibold text-slate-900">
              {prepared.invoiceIds.length} facturas ·{" "}
              {prepared.transactionIds.length} transacciones
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Confirmada{" "}
              {new Date(prepared.preparedAt).toLocaleString("es-CO")}. La
              extracción aún no se ha iniciado.
            </p>
            <p className="mt-3 text-xs text-slate-500">
              Esta confirmación prepara los parámetros del entregable 2; la
              ejecución y exportación se desarrollarán en el entregable 3.
            </p>
            <button
              type="button"
              onClick={() => setPrepared(null)}
              className="mt-3 text-sm font-medium text-slate-500 hover:text-slate-800"
            >
              Ocultar resumen
            </button>
          </section>
        )}
      </main>

      {detailInvoiceId && (
        <InvoiceDetail
          invoiceId={detailInvoiceId}
          onClose={() => setDetailInvoiceId(null)}
        />
      )}
    </div>
  );
}
