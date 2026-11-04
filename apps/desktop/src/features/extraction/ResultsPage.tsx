import { useMemo, useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Link, useParams } from "react-router-dom";

import { ThemeToggle } from "../theme/ThemeToggle";
import { extractionRunApi, RESULT_PAGE_SIZE } from "./extractionRunApi";
import {
  DATASETS,
  hasResults,
  isActive,
  STATUS_LABELS,
  type DatasetKey,
} from "./runTypes";

type Row = Record<string, string | null>;
const card = "rounded-2xl border border-slate-200 bg-white p-5 shadow-sm";

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-800">{value}</p>
    </div>
  );
}

const fmt = (v: string | null) => (v ? new Date(v).toLocaleString("es-CO") : "—");

export function ResultsPage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const [dataset, setDataset] = useState<DatasetKey>("consulta");
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");

  const execution = useQuery({
    queryKey: ["extraction", id],
    queryFn: () => extractionRunApi.get(id),
    // Seguimiento por sondeo mientras la ejecución esté activa.
    refetchInterval: (q) => (q.state.data && isActive(q.state.data.status) ? 1500 : false),
  });
  const status = execution.data?.status;
  const ready = status ? hasResults(status) : false;

  const results = useQuery({
    queryKey: ["extraction-results", id, dataset, page, search],
    queryFn: () => extractionRunApi.results(id, dataset, page, search),
    enabled: ready,
    placeholderData: keepPreviousData,
  });

  const cancel = useMutation({
    mutationFn: () => extractionRunApi.cancel(id),
    onSuccess: (data) => queryClient.setQueryData(["extraction", id], data),
  });
  const exportExcel = useMutation({ mutationFn: () => extractionRunApi.exportExcel(id) });

  const columns = useMemo<ColumnDef<Row>[]>(
    () =>
      (results.data?.columns ?? []).map((name) => ({
        accessorKey: name,
        header: name,
        cell: (info) => info.getValue<string | null>() ?? "—",
      })),
    [results.data?.columns],
  );
  const table = useReactTable({
    data: results.data?.items ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    rowCount: results.data?.total ?? 0,
  });

  const totalPages = Math.max(1, Math.ceil((results.data?.total ?? 0) / RESULT_PAGE_SIZE));
  const e = execution.data;
  const metrics = e?.metrics;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[1500px] items-center justify-between gap-3 px-6 py-4">
          <div className="flex items-center gap-3">
            <Link to="/generation" className="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50">
              ← Generación
            </Link>
            <h1 className="text-lg font-semibold text-slate-900">Resultados de extracción RIPS</h1>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto max-w-[1500px] space-y-5 px-6 py-6">
        {execution.isPending && <p className="text-sm text-slate-500">Consultando ejecución…</p>}
        {execution.isError && (
          <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{execution.error.message}</p>
        )}

        {e && metrics && (
          <>
            <section className={card}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-widest text-blue-600">
                    {STATUS_LABELS[e.status]}
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    {e.current_step ?? ""} · Inicio {fmt(e.started_at)} · Fin {fmt(e.finished_at)}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    Contratos: {e.contracts.length ? e.contracts.join(", ") : "—"}
                  </p>
                </div>
                <div className="flex gap-2">
                  {isActive(e.status) && (
                    <button type="button" disabled={cancel.isPending} onClick={() => cancel.mutate()}
                      className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50">
                      Cancelar
                    </button>
                  )}
                  <button type="button" disabled={!ready || exportExcel.isPending} onClick={() => exportExcel.mutate()}
                    className="rounded-lg bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-40">
                    {exportExcel.isPending ? "Generando…" : "Exportar RIPS a Excel"}
                  </button>
                </div>
              </div>

              {isActive(e.status) && (
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100" role="progressbar"
                  aria-valuenow={e.progress} aria-valuemin={0} aria-valuemax={100}>
                  <div className="h-full bg-blue-600 transition-all" style={{ width: e.progress + "%" }} />
                </div>
              )}

              <div className="mt-4 grid gap-3 sm:grid-cols-3 xl:grid-cols-6">
                <Metric label="Facturas consultadas" value={metrics.invoices_consulted} />
                <Metric label="Facturas válidas" value={metrics.invoices_valid} />
                <Metric label="Facturas corregidas" value={metrics.invoices_corrected} />
                <Metric label="Facturas descartadas" value={metrics.invoices_discarded} />
                <Metric label="Transacciones procesadas" value={metrics.transactions_processed} />
                <Metric label="Transacciones encontradas" value={metrics.transactions_found} />
              </div>
              <div className="mt-3 grid gap-3 sm:grid-cols-4">
                {DATASETS.slice(0, 4).map((d) => (
                  <Metric key={d.key} label={d.label} value={metrics.records_by_category[d.key] ?? 0} />
                ))}
              </div>

              {exportExcel.data && (
                <p role="status" className="mt-4 text-sm text-emerald-700">
                  Archivo generado: <span className="font-mono">{exportExcel.data.path}</span>
                </p>
              )}
              {exportExcel.isError && (
                <p role="alert" className="mt-4 text-sm text-red-700">{exportExcel.error.message}</p>
              )}
            </section>

            {e.errors.map((m) => (
              <div key={m} role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{m}</div>
            ))}
            {e.warnings.map((m) => (
              <div key={m} role="status" className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{m}</div>
            ))}

            {ready && (
              <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-3">
                  <div className="flex flex-wrap gap-1">
                    {DATASETS.map((d) => (
                      <button key={d.key} type="button"
                        onClick={() => { setDataset(d.key); setPage(1); }}
                        className={"rounded-md px-3 py-1.5 text-xs font-semibold " +
                          (dataset === d.key ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-100")}>
                        {d.label}
                      </button>
                    ))}
                  </div>
                  <form onSubmit={(ev) => { ev.preventDefault(); setSearch(searchInput); setPage(1); }}>
                    <input value={searchInput} onChange={(ev) => setSearchInput(ev.target.value)}
                      placeholder="Buscar en la tabla"
                      className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm" />
                  </form>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                      {table.getHeaderGroups().map((g) => (
                        <tr key={g.id}>
                          {g.headers.map((h) => (
                            <th key={h.id} className="whitespace-nowrap px-4 py-3">
                              {flexRender(h.column.columnDef.header, h.getContext())}
                            </th>
                          ))}
                        </tr>
                      ))}
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {table.getRowModel().rows.map((row) => (
                        <tr key={row.id} className="hover:bg-slate-50/80">
                          {row.getVisibleCells().map((cell) => (
                            <td key={cell.id} className="whitespace-nowrap px-4 py-2 text-slate-700">
                              {flexRender(cell.column.columnDef.cell, cell.getContext())}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {results.data?.items.length === 0 && (
                    <p className="px-5 py-10 text-center text-sm text-slate-500">Sin registros.</p>
                  )}
                </div>

                <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-xs text-slate-500">
                  <span>{(results.data?.total ?? 0).toLocaleString("es-CO")} registros</span>
                  <div className="flex items-center gap-2">
                    <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}
                      className="rounded-md border border-slate-300 px-3 py-1.5 disabled:opacity-40">Anterior</button>
                    <span>Página {page} de {totalPages}</span>
                    <button type="button" disabled={page >= totalPages} onClick={() => setPage(page + 1)}
                      className="rounded-md border border-slate-300 px-3 py-1.5 disabled:opacity-40">Siguiente</button>
                  </div>
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}