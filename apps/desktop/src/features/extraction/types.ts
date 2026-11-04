/** Contratos TypeScript alineados con los esquemas Pydantic del backend. */

export interface CatalogItem {
  value: string;
  label: string;
}

export type InvoiceSource = "base_fixed" | "sql_server";

export interface Invoice {
  id: string;
  invoice: string;
  nit_provider: string;
  provider_name: string | null;
  contract: string;
  service_month: string | null;
  invoice_date: string | null;
  filing_date: string | null;
  billed_amount: string | number | null;
  source: InvoiceSource;
}

export interface InvoiceDataset {
  items: Invoice[];
  total: number;
  warnings: string[];
}

export interface InvoicePage {
  items: Invoice[];
  total: number;
  page: number;
  page_size: number;
  warnings: string[];
}

export interface Transaction {
  id: string;
  invoice: string;
  contract: string;
  nit_provider: string;
  provider_code: string | null;
  rips_date: string | null;
  filing_date: string | null;
}

export interface TransactionDataset {
  items: Transaction[];
  total: number;
}

export interface TransactionPage {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
}

export interface InvoiceFilters {
  contract: string;
  provider_nit: string;
  invoice: string;
  start_date: string;
  end_date: string;
}

export interface PreparedSelection {
  status: "prepared";
  prepared_at: string;
  invoice_ids: string[];
  transaction_ids: string[];
  invoice_count: number;
  transaction_count: number;
  contracts: string[];
  providers: string[];
}
