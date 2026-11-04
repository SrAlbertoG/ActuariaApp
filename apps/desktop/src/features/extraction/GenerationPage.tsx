import { useEffect, useMemo, useState, type FormEvent, type KeyboardEvent } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { extractionApi, PAGE_SIZE } from "./extractionApi";
import { ThemeToggle } from "../theme/ThemeToggle";
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

const MAX_SELECTED_INVOICES = 1000;
const MAX_SELECTED_TRANSACTIONS = 1000;

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
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [showContractSuggestions, setShowContractSuggestions] = useState(false);
  const [showProviderSuggestions, setShowProviderSuggestions] = useState(false);
  const [activeContractSuggestion, setActiveContractSuggestion] = useState(0);
  const [activeProviderSuggestion, setActiveProviderSuggestion] = useState(0);
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

  // Los catálogos se consultan al entrar a la pantalla, no por cada tecla.
  // React Query conserva la respuesta durante 5 minutos y la renueva al volver
  // a entrar si ya venció ese tiempo.
  const contracts = useQuery({
    queryKey: ["invoice-contracts"],
    queryFn: () => extractionApi.getContracts(),
    staleTime: 5 * 60 * 1000,
    refetchOnMount: true,
    refetchOnWindowFocus: false,
  });

  const providers = useQuery({
    queryKey: ["invoice-providers"],
    // Catálogo completo al entrar: el NIT se filtra localmente mientras se escribe.
    queryFn: () => extractionApi.getProviders(),
    staleTime: 5 * 60 * 1000,
    refetchOnMount: true,
    refetchOnWindowFocus: false,
  });

  const contractOptions = useMemo(() => {
    const search = filters.contract.trim().toLocaleLowerCase("es");
    const items = contracts.data ?? [];
    return search
      ? items.filter((item) =>
          item.value.toLocaleLowerCase("es").includes(search) ||
          item.label.toLocaleLowerCase("es").includes(search),
        )
      : items;
  }, [contracts.data, filters.contract]);

  const providerOptions = useMemo(() => {
    const search = filters.provider_nit.trim().toLocaleLowerCase("es");
    return (providers.data ?? []).filter((item) =>
      !search ||
      item.value.toLocaleLowerCase("es").includes(search) ||
      item.label.toLocaleLowerCase("es").includes(search),
    );
  }, [providers.data, filters.provider_nit]);

  // Se descarga una sola vez el conjunto acotado; la paginación es local.
  const invoices = useQuery({
    queryKey: ["invoice-dataset", appliedFilters],
    queryFn: () => extractionApi.searchInvoiceDataset(appliedFilters),
    enabled: hasSearched,
    staleTime: 60 * 1000,
  });

  const selectedInvoiceIds = useMemo(
    () => Object.keys(selectedInvoices).sort(),
    [selectedInvoices],
  );

  const transactions = useQuery({
    queryKey: ["transactions", selectedInvoiceIds, appliedFilters],
    queryFn: () =>
      extractionApi.searchAllTransactions(selectedInvoiceIds, appliedFilters),
    enabled: selectedInvoiceIds.length > 0,
  });

  const allInvoiceRows = invoices.data?.items ?? [];
  const invoiceRows = allInvoiceRows.slice(
    (invoicePage - 1) * PAGE_SIZE,
    invoicePage * PAGE_SIZE,
  );
  const allTransactionRows = transactions.data?.items ?? [];
  const transactionRows = allTransactionRows.slice(
    (transactionPage - 1) * PAGE_SIZE,
    transactionPage * PAGE_SIZE,
  );

  const selectedInvoiceCount = selectedInvoiceIds.length;
  const selectedTransactionIds = Object.keys(selectedTransactions);
  const allInvoicesSelected =
    Boolean(invoices.data?.total) &&
    selectedInvoiceCount === invoices.data?.total;
  const allTransactionsSelected =
    allTransactionRows.length > 0 &&
    allTransactionRows.every((transaction) =>
      Boolean(selectedTransactions[transaction.id]),
    );

  // La consulta recupera los registros de todas las páginas. Preselecciona
  // los que cumplen los filtros originales y conserva los cambios manuales.
  useEffect(() => {
    if (!allTransactionRows.length) return;
    setSelectedTransactions((current) => {
      const next = { ...current };
      for (const transaction of allTransactionRows) {
        if (
          Object.keys(next).length < MAX_SELECTED_TRANSACTIONS ||
          next[transaction.id]
        ) {
          next[transaction.id] = transaction;
        }
      }
      return next;
    });
  }, [allTransactionRows]);

  const preparation = useMutation({
    mutationFn: () =>
      extractionApi.prepareSelection(
        selectedInvoiceIds,
        selectedTransactionIds,
        appliedFilters,
      ),
    onSuccess: (result) => setPrepared(result),
  });

  const handleFilterChange = (
    field: keyof InvoiceFilters,
    value: string,
  ) => {
    setFilters((current) => ({
      ...current,
      [field]: value,
      ...(field === "contract" ? { provider_nit: "" } : {}),
    }));
    if (field === "contract") setActiveContractSuggestion(0);
    if (field === "provider_nit") setActiveProviderSuggestion(0);
    setFilterError(null);
    setSelectionError(null);
  };

  const handleContractKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    const options = contractOptions.slice(0, 12);
    if (event.key === "Escape") {
      setShowContractSuggestions(false);
      return;
    }
    if (!showContractSuggestions || !filters.contract.trim() || !options.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveContractSuggestion((current) => Math.min(current + 1, options.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveContractSuggestion((current) => Math.max(current - 1, 0));
    } else if (event.key === "Enter" && options[activeContractSuggestion]) {
      event.preventDefault();
      handleFilterChange("contract", options[activeContractSuggestion].value);
      setShowContractSuggestions(false);
    }
  };

  const handleProviderKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    const options = providerOptions.slice(0, 12);
    if (event.key === "Escape") {
      setShowProviderSuggestions(false);
      return;
    }
    if (!showProviderSuggestions || !filters.provider_nit.trim() || !options.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveProviderSuggestion((current) => Math.min(current + 1, options.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveProviderSuggestion((current) => Math.max(current - 1, 0));
    } else if (event.key === "Enter" && options[activeProviderSuggestion]) {
      event.preventDefault();
      handleFilterChange("provider_nit", options[activeProviderSuggestion].value);
      setShowProviderSuggestions(false);
    }
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
    setSelectionError(null);
    setPrepared(null);
    preparation.reset();
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
    setSelectionError(null);
    setPrepared(null);
    preparation.reset();
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
      const invoiceStillSelected = Object.values(selectedInvoices).some(
        (selectedInvoice) =>
          selectedInvoice.id !== invoice.id &&
          selectedInvoice.invoice === invoice.invoice &&
          selectedInvoice.nit_provider === invoice.nit_provider &&
          selectedInvoice.contract === invoice.contract,
      );

      if (!invoiceStillSelected) {
        setSelectedTransactions((current) => {
          const next = { ...current };
          Object.keys(next).forEach((id) => {
            const transaction = next[id];
            if (
              transaction.invoice === invoice.invoice &&
              transaction.nit_provider === invoice.nit_provider &&
              transaction.contract === invoice.contract
            ) {
              delete next[id];
            }
          });
          return next;
        });
      }
    }

    setTransactionPage(1);
    setPrepared(null);
    preparation.reset();
  };

  const toggleAllInvoices = async (checked: boolean) => {
    setSelectionError(null);
    if (!checked) {
      setSelectedInvoices({});
      setSelectedTransactions({});
      setTransactionPage(1);
      setPrepared(null);
      preparation.reset();
      return;
    }

    // El conjunto completo ya está en memoria: reflejar la selección en el
    // checkbox inmediatamente, sin esperar ninguna consulta de transacciones.
    if (allInvoiceRows.length > MAX_SELECTED_INVOICES) {
      setSelectionError("La selección supera el máximo de 1.000 facturas.");
      return;
    }
    setSelectedInvoices(
      Object.fromEntries(allInvoiceRows.map((invoice) => [invoice.id, invoice])),
    );
    setSelectedTransactions({});
    setTransactionPage(1);
    setPrepared(null);
    preparation.reset();
  };

  const toggleTransaction = (
    transaction: Transaction,
    checked: boolean,
  ) => {
    setSelectedTransactions((current) => {
      const next = { ...current };
      if (checked) {
        if (
          Object.keys(next).length < MAX_SELECTED_TRANSACTIONS ||
          next[transaction.id]
        ) {
          next[transaction.id] = transaction;
        }
      } else {
        delete next[transaction.id];
      }
      return next;
    });
    setPrepared(null);
    preparation.reset();
  };

  const toggleAllTransactions = (checked: boolean) => {
    setSelectedTransactions((current) => {
      const next = { ...current };
      allTransactionRows.forEach((transaction) => {
        if (checked) {
          if (
            Object.keys(next).length < MAX_SELECTED_TRANSACTIONS ||
            next[transaction.id]
          ) {
            next[transaction.id] = transaction;
          }
        } else {
          delete next[transaction.id];
        }
      });
      return next;
    });
    setSelectionError(null);
    setPrepared(null);
    preparation.reset();
  };

  const handlePrepare = () => {
    if (selectedInvoiceCount === 0 || selectedTransactionIds.length === 0) {
      return;
    }

    // El backend comprueba los identificadores y el estado activo de RIPS.
    // Esta llamada no inicia la extracción, que pertenece al entregable 3.
    preparation.mutate();
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
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
              Conexión SQL activa
            </span>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1500px] space-y-5 px-6 py-6">
        <section>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-slate-900">
                Parámetros de búsqueda
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Filtra las facturas y selecciona las transacciones que participarán
                en la extracción.
              </p>
              <p className="mt-1 text-xs text-slate-500" role="status">
                {contracts.isPending || providers.isPending
                  ? "Cargando catálogos de contratos y prestadores…"
                  : contracts.isError || providers.isError
                    ? "No se pudieron cargar todos los catálogos. Puedes intentar actualizarlos."
                    : "Catálogos disponibles: " + (contracts.data?.length ?? 0) + " contratos y " + (providers.data?.length ?? 0) + " prestadores."}
              </p>
            </div>
            <button
              type="button"
              onClick={() => void Promise.all([contracts.refetch(), providers.refetch()])}
              disabled={contracts.isFetching || providers.isFetching}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-wait disabled:opacity-50"
            >
              {contracts.isFetching || providers.isFetching
                ? "Actualizando catálogos…"
                : "Actualizar catálogos"}
            </button>
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
                <div className="relative">
                  <input
                    id="contract"
                    role="combobox"
                    aria-autocomplete="list"
                    aria-expanded={showContractSuggestions}
                    aria-controls="contract-suggestions"
                    aria-activedescendant={
                      showContractSuggestions
                        ? `contract-option-${activeContractSuggestion}`
                        : undefined
                    }
                    autoComplete="off"
                    className={inputClass}
                    placeholder="Escribe para buscar o ingresar un contrato"
                    value={filters.contract}
                    onFocus={() => setShowContractSuggestions(true)}
                    onBlur={() => setShowContractSuggestions(false)}
                    onKeyDown={handleContractKeyDown}
                    onChange={(event) =>
                      handleFilterChange("contract", event.target.value)
                    }
                  />
                  {showContractSuggestions && filters.contract.trim() && (
                    <ul
                      id="contract-suggestions"
                      role="listbox"
                      className="mt-1 max-h-56 w-full overflow-y-auto rounded-lg border border-slate-200 bg-white py-1 shadow-sm"
                    >
                      {contracts.isPending && !contracts.data ? (
                        <li className="px-3 py-2 text-xs text-slate-500">
                          Cargando catálogo de contratos…
                        </li>
                      ) : contractOptions.length ? (
                        contractOptions.slice(0, 12).map((item, index) => (
                          <li
                            key={item.value}
                            id={`contract-option-${index}`}
                            role="option"
                            aria-selected={activeContractSuggestion === index}
                          >
                            <button
                              type="button"
                              className={
                                "w-full px-3 py-2 text-left text-sm " +
                                (activeContractSuggestion === index
                                  ? "bg-blue-50 text-blue-800"
                                  : "text-slate-700 hover:bg-slate-100")
                              }
                              onMouseEnter={() => setActiveContractSuggestion(index)}
                              onMouseDown={(event) => event.preventDefault()}
                              onClick={() => {
                                handleFilterChange("contract", item.value);
                                setShowContractSuggestions(false);
                              }}
                            >
                              {item.label}
                            </button>
                          </li>
                        ))
                      ) : (
                        <li className="px-3 py-2 text-xs text-slate-500">
                          Sin coincidencias. Puedes conservar el texto escrito.
                        </li>
                      )}
                    </ul>
                  )}
                </div>
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
                <div className="relative">
                  <input
                    id="provider"
                    role="combobox"
                    aria-autocomplete="list"
                    aria-expanded={showProviderSuggestions}
                    aria-controls="provider-suggestions"
                    aria-activedescendant={
                      showProviderSuggestions
                        ? `provider-option-${activeProviderSuggestion}`
                        : undefined
                    }
                    autoComplete="off"
                    inputMode="numeric"
                    className={inputClass}
                    placeholder="Escribe NIT para buscar"
                    value={filters.provider_nit}
                    onFocus={() => setShowProviderSuggestions(true)}
                    onBlur={() => setShowProviderSuggestions(false)}
                    onKeyDown={handleProviderKeyDown}
                    onChange={(event) =>
                      handleFilterChange("provider_nit", event.target.value)
                    }
                  />
                  {showProviderSuggestions && filters.provider_nit.trim() && (
                    <ul
                      id="provider-suggestions"
                      role="listbox"
                      className="mt-1 max-h-56 w-full overflow-y-auto rounded-lg border border-slate-200 bg-white py-1 shadow-sm"
                    >
                      {providers.isPending && !providers.data ? (
                        <li className="px-3 py-2 text-xs text-slate-500">
                          Cargando catálogo de prestadores…
                        </li>
                      ) : providerOptions.length ? (
                        providerOptions.slice(0, 12).map((item, index) => (
                          <li
                            key={item.value}
                            id={`provider-option-${index}`}
                            role="option"
                            aria-selected={activeProviderSuggestion === index}
                          >
                            <button
                              type="button"
                              className={
                                "w-full px-3 py-2 text-left text-sm " +
                                (activeProviderSuggestion === index
                                  ? "bg-blue-50 text-blue-800"
                                  : "text-slate-700 hover:bg-slate-100")
                              }
                              onMouseEnter={() => setActiveProviderSuggestion(index)}
                              onMouseDown={(event) => event.preventDefault()}
                              onClick={() => {
                                handleFilterChange("provider_nit", item.value);
                                setShowProviderSuggestions(false);
                              }}
                            >
                              <span className="block font-medium">{item.value}</span>
                              <span className="block text-xs text-slate-500">{item.label}</span>
                            </button>
                          </li>
                        ))
                      ) : (
                        <li className="px-3 py-2 text-xs text-slate-500">
                          Sin coincidencias. Puedes conservar el NIT escrito.
                        </li>
                      )}
                    </ul>
                  )}
                </div>
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
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                {selectedInvoiceCount} seleccionadas
              </span>
              <span className="text-xs text-slate-500">
                {invoices.data?.total.toLocaleString("es-CO") ?? "—"} resultados
              </span>
              <button
                type="button"
                disabled={!invoices.data?.total}
                onClick={() => void toggleAllInvoices(!allInvoicesSelected)}
                className="rounded-lg border border-blue-200 px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
{allInvoicesSelected
                  ? "Quitar selección global"
                  : "Seleccionar todas"}
              </button>
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
                          aria-label="Seleccionar todas las facturas encontradas"
                          checked={allInvoicesSelected}
                          onChange={(event) =>
                            void toggleAllInvoices(event.target.checked)
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
              {selectionError && (
                <p role="alert" className="px-5 pb-3 text-xs text-red-700">
                  {selectionError}
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
                Transacciones activas que coinciden con los filtros originales de búsqueda.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                {selectedTransactionIds.length} transacciones seleccionadas
              </span>
              <button
                type="button"
                disabled={!allTransactionRows.length || transactions.isPending}
                onClick={() => toggleAllTransactions(!allTransactionsSelected)}
                className="rounded-lg border border-blue-200 px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {allTransactionsSelected
                  ? "Quitar selección global"
                  : "Seleccionar todas las transacciones"}
              </button>
            </div>
          </div>

          {selectedTransactionIds.length >= MAX_SELECTED_TRANSACTIONS && (
            <p className="border-b border-amber-100 bg-amber-50 px-5 py-2 text-xs text-amber-800">
              Has alcanzado el máximo de {MAX_SELECTED_TRANSACTIONS} transacciones por preparación.
            </p>
          )}

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
                          aria-label="Seleccionar todas las transacciones encontradas"
                          checked={allTransactionsSelected}
                          onChange={(event) =>
                            toggleAllTransactions(event.target.checked)
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
              {selectionError && (
                <p role="alert" className="px-5 pb-3 text-xs text-red-700">
                  {selectionError}
                </p>
              )}
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
              selectedInvoiceCount === 0 ||
              selectedTransactionIds.length === 0 ||
              preparation.isPending
            }
            className="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {preparation.isPending
              ? "Validando selección…"
              : "Confirmar selección"}
          </button>
        </section>

        {preparation.isError && (
          <p role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {preparation.error.message}
          </p>
        )}

        {prepared && (
          <section
            role="status"
            className="rounded-2xl border border-emerald-200 bg-white p-5 shadow-sm"
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-emerald-700">
              Selección preparada
            </p>
            <h2 className="mt-1 text-lg font-semibold text-slate-900">
              {prepared.invoice_count} facturas ·{" "}
              {prepared.transaction_count} transacciones
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Confirmada{" "}
              {new Date(prepared.prepared_at).toLocaleString("es-CO")}. La
              extracción aún no se ha iniciado.
            </p>
            <div className="mt-3 grid gap-3 text-xs text-slate-600 sm:grid-cols-2">
              <div>
                <p className="font-semibold text-slate-700">Contratos RIPS</p>
                <p>{prepared.contracts.length ? prepared.contracts.join(", ") : "No disponible"}</p>
              </div>
              <div>
                <p className="font-semibold text-slate-700">NIT de prestadores</p>
                <p>{prepared.providers.length ? prepared.providers.join(", ") : "No disponible"}</p>
              </div>
            </div>
            <p className="mt-3 text-xs text-slate-500">
              La selección fue validada por FastAPI. La ejecución y exportación
              se desarrollarán en el entregable 3.
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
