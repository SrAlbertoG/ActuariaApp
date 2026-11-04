/** Debe coincidir exactamente con ExtractionStatus del backend. */
export const EXECUTION_STATUSES = [
  "queued",
  "running",
  "completed",
  "completed_with_warnings",
  "failed",
  "cancelled",
] as const;
export type ExecutionStatus = (typeof EXECUTION_STATUSES)[number];

export const isActive = (s: ExecutionStatus) => s === "queued" || s === "running";
export const hasResults = (s: ExecutionStatus) =>
  s === "completed" || s === "completed_with_warnings";

export const STATUS_LABELS: Record<ExecutionStatus, string> = {
  queued: "En espera",
  running: "En ejecución",
  completed: "Finalizada",
  completed_with_warnings: "Finalizada con advertencias",
  failed: "Con error",
  cancelled: "Cancelada",
};

export const DATASETS = [
  { key: "consulta", label: "Consultas" },
  { key: "procedimiento", label: "Procedimientos" },
  { key: "medicamento", label: "Medicamentos" },
  { key: "insumo", label: "Insumos" },
  { key: "facturas", label: "Facturas" },
  { key: "transacciones", label: "Transacciones" },
] as const;
export type DatasetKey = (typeof DATASETS)[number]["key"];

export interface ExtractionMetrics {
  invoices_consulted: number;
  invoices_valid: number;
  invoices_corrected: number;
  invoices_discarded: number;
  transactions_selected: number;
  transactions_found: number;
  transactions_processed: number;
  records_by_category: Record<string, number>;
}

export interface Extraction {
  execution_id: string;
  status: ExecutionStatus;
  progress: number;
  current_step: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  contracts: string[];
  parameters: Record<string, unknown>;
  metrics: ExtractionMetrics;
  warnings: string[];
  errors: string[];
  export_path: string | null;
}

export interface ExtractionCreated {
  execution_id: string;
  status: ExecutionStatus;
  message: string;
}

export interface ResultPage {
  dataset: DatasetKey;
  columns: string[];
  items: Record<string, string | null>[];
  total: number;
  page: number;
  page_size: number;
}

export interface ExportInfo {
  execution_id: string;
  filename: string;
  path: string;
  size_bytes: number;
  generated_at: string;
}