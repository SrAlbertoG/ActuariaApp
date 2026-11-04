import { apiFetch } from "../../lib/api";
import type {
  CatalogItem,
  Invoice,
  InvoiceFilters,
  InvoicePage,
  TransactionPage,
  PreparedSelection,
} from "./types";

export const PAGE_SIZE = 25;
const BULK_PAGE_SIZE = 100;
const MAX_BULK_INVOICES = 1000;
const MAX_BULK_TRANSACTIONS = 1000;

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

  searchInvoices(
    filters: InvoiceFilters,
    page: number,
    pageSize = PAGE_SIZE,
  ): Promise<InvoicePage> {
    const params = buildQuery(filters);
    params.set("page", String(page));
    params.set("page_size", String(pageSize));

    return apiFetch<InvoicePage>("/invoices?" + params.toString());
  },

  async searchAllInvoices(filters: InvoiceFilters): Promise<Invoice[]> {
    const firstPage = await this.searchInvoices(filters, 1, BULK_PAGE_SIZE);
    if (firstPage.total > MAX_BULK_INVOICES) {
      throw new Error(
        `La búsqueda encontró ${firstPage.total} facturas. Para seleccionar todas a la vez, reduce los filtros a máximo ${MAX_BULK_INVOICES} facturas.`,
      );
    }

    const pages = Math.ceil(firstPage.total / BULK_PAGE_SIZE);
    const remaining = await Promise.all(
      Array.from({ length: Math.max(0, pages - 1) }, (_, index) =>
        this.searchInvoices(filters, index + 2, BULK_PAGE_SIZE),
      ),
    );
    return [
      ...firstPage.items,
      ...remaining.flatMap((page) => page.items),
    ];
  },

  getInvoice(invoiceId: string): Promise<Invoice> {
    return apiFetch<Invoice>("/invoices/" + encodeURIComponent(invoiceId));
  },

  searchTransactions(
    invoiceIds: string[],
    filters: InvoiceFilters,
    page: number,
    pageSize = PAGE_SIZE,
  ): Promise<TransactionPage> {
    return apiFetch<TransactionPage>("/transactions/search", {
      method: "POST",
      body: JSON.stringify({
        invoice_ids: invoiceIds,
        contract: filters.contract.trim() || null,
        provider_nit: filters.provider_nit.trim() || null,
        invoice: filters.invoice.trim() || null,
        page,
        page_size: pageSize,
      }),
    });
  },

  async searchAllTransactions(
    invoiceIds: string[],
    filters: InvoiceFilters,
  ): Promise<TransactionPage> {
    const firstPage = await this.searchTransactions(
      invoiceIds,
      filters,
      1,
      BULK_PAGE_SIZE,
    );
    if (firstPage.total > MAX_BULK_TRANSACTIONS) {
      throw new Error(
        `Se encontraron ${firstPage.total} transacciones coincidentes. Reduce los filtros o las facturas seleccionadas para no superar el límite de ${MAX_BULK_TRANSACTIONS} transacciones.`,
      );
    }

    const pages = Math.ceil(firstPage.total / BULK_PAGE_SIZE);
    const remaining = await Promise.all(
      Array.from({ length: Math.max(0, pages - 1) }, (_, index) =>
        this.searchTransactions(
          invoiceIds,
          filters,
          index + 2,
          BULK_PAGE_SIZE,
        ),
      ),
    );
    const items = [
      ...firstPage.items,
      ...remaining.flatMap((page) => page.items),
    ];
    return { ...firstPage, items };
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
