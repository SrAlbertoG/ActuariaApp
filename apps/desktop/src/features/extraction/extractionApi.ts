import { apiFetch } from "../../lib/api";
import type {
  CatalogItem,
  Invoice,
  InvoiceFilters,
  InvoiceDataset,
  TransactionDataset,
  TransactionPage,
  PreparedSelection,
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

  searchInvoiceDataset(filters: InvoiceFilters): Promise<InvoiceDataset> {
    const params = buildQuery(filters);
    return apiFetch<InvoiceDataset>("/invoices/dataset?" + params.toString());
  },

  async searchAllInvoices(filters: InvoiceFilters): Promise<Invoice[]> {
    // Compatibilidad para consumidores existentes; el backend devuelve el dataset en una sola llamada.
    return (await this.searchInvoiceDataset(filters)).items;
  },

  getInvoice(invoiceId: string): Promise<Invoice> {
    return apiFetch<Invoice>("/invoices/" + encodeURIComponent(invoiceId));
  },

  searchAllTransactions(
    invoiceIds: string[],
    filters: InvoiceFilters,
  ): Promise<TransactionDataset> {
    return apiFetch<TransactionDataset>("/transactions/dataset", {
      method: "POST",
      body: JSON.stringify({
        invoice_ids: invoiceIds,
        contract: filters.contract.trim() || null,
        provider_nit: filters.provider_nit.trim() || null,
        invoice: filters.invoice.trim() || null,
      }),
    });
  },

  prepareSelection(
    invoiceIds: string[],
    transactionIds: string[],
    filters: InvoiceFilters,
  ): Promise<PreparedSelection> {
    return apiFetch<PreparedSelection>("/extraction/prepare", {
      method: "POST",
      body: JSON.stringify({
        invoice_ids: invoiceIds,
        transaction_ids: transactionIds,
        contract: filters.contract.trim() || null,
        provider_nit: filters.provider_nit.trim() || null,
        invoice: filters.invoice.trim() || null,
      }),
    });
  },
};
