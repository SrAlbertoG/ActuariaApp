import { apiFetch } from "../../lib/api";
import type {
  DatasetKey,
  ExportInfo,
  Extraction,
  ExtractionCreated,
  ResultPage,
} from "./runTypes";
import type { InvoiceFilters, PreparedSelection } from "./types";

export const RESULT_PAGE_SIZE = 50;

export const extractionRunApi = {
  create(prepared: PreparedSelection, filters: InvoiceFilters): Promise<ExtractionCreated> {
    return apiFetch<ExtractionCreated>("/extractions", {
      method: "POST",
      body: JSON.stringify({
        invoice_ids: prepared.invoice_ids,
        transaction_ids: prepared.transaction_ids,
        contracts: filters.contract.trim() ? [filters.contract.trim()] : [],
        providers: prepared.providers,
        start_date: filters.start_date || null,
        end_date: filters.end_date || null,
        contract: filters.contract.trim() || null,
        provider_nit: filters.provider_nit.trim() || null,
        invoice: filters.invoice.trim() || null,
        categories: ["consulta", "procedimiento", "medicamento", "insumo"],
        homologate: false,
      }),
    });
  },

  get: (id: string) => apiFetch<Extraction>("/extractions/" + encodeURIComponent(id)),

  cancel: (id: string) =>
    apiFetch<Extraction>("/extractions/" + encodeURIComponent(id) + "/cancel", { method: "POST" }),

  results(id: string, dataset: DatasetKey, page: number, search: string): Promise<ResultPage> {
    const params = new URLSearchParams({
      dataset,
      page: String(page),
      page_size: String(RESULT_PAGE_SIZE),
    });
    if (search.trim()) params.set("search", search.trim());
    return apiFetch<ResultPage>(
      "/extractions/" + encodeURIComponent(id) + "/results?" + params.toString(),
    );
  },

  exportExcel: (id: string) =>
    apiFetch<ExportInfo>("/exports/" + encodeURIComponent(id), { method: "POST" }),
};