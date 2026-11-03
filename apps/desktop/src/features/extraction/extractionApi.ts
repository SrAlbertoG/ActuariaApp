import { apiFetch } from "../../lib/api";
import type {
  CatalogItem,
  Invoice,
  InvoiceFilters,
  InvoicePage,
  TransactionPage,
} from "./types";

export const PAGE_SIZE = 25;

/** Serializa filtros omitiendo los valores vacíos. */
function buildQuery(filters: Partial<InvoiceFilters> = {}): URLSearchParams {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value && value.trim()) params.set(key, value.trim());
  });

  return params;
}

export const extractionApi = {
  getContracts(search?: string): Promise<CatalogItem[]> {
    const params = new URLSearchParams();
    if (search && search.trim()) params.set("search", search.trim());

    const query = params.toString();
    const suffix = query ? "?" + query : "";
    return apiFetch<CatalogItem[]>("/contracts" + suffix);
  },

  getProviders(contract?: string, search?: string): Promise<CatalogItem[]> {
    const params = new URLSearchParams();
    if (contract) params.set("contract", contract);
    if (search && search.trim()) params.set("search", search.trim());

    const query = params.toString();
    const suffix = query ? "?" + query : "";
    return apiFetch<CatalogItem[]>("/providers" + suffix);
  },

  searchInvoices(filters: InvoiceFilters, page: number): Promise<InvoicePage> {
    const params = buildQuery(filters);
    params.set("page", String(page));
    params.set("page_size", String(PAGE_SIZE));

    return apiFetch<InvoicePage>("/invoices?" + params.toString());
  },

  getInvoice(invoiceId: string): Promise<Invoice> {
    return apiFetch<Invoice>("/invoices/" + encodeURIComponent(invoiceId));
  },

  searchTransactions(
    invoiceIds: string[],
    page: number,
  ): Promise<TransactionPage> {
    return apiFetch<TransactionPage>("/transactions/search", {
      method: "POST",
      body: JSON.stringify({
        invoice_ids: invoiceIds,
        page,
        page_size: PAGE_SIZE,
      }),
    });
  },
};
