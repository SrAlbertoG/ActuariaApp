import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { extractionRunApi } from "./extractionRunApi";
import type { InvoiceFilters, PreparedSelection } from "./types";

/** Inicia la extracción con la selección ya validada y abre la pantalla de seguimiento. */
export function StartExtractionButton({
  prepared,
  filters,
}: {
  prepared: PreparedSelection;
  filters: InvoiceFilters;
}) {
  const navigate = useNavigate();
  const start = useMutation({
    mutationFn: () => extractionRunApi.create(prepared, filters),
    onSuccess: (created) => navigate("/extractions/" + created.execution_id),
  });

  return (
    <div className="mt-3 inline-block">
      <button
        type="button"
        disabled={start.isPending}
        onClick={() => start.mutate()}
        className="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-800 disabled:opacity-40"
      >
        {start.isPending ? "Iniciando…" : "Iniciar extracción RIPS"}
      </button>
      {start.isError && (
        <p role="alert" className="mt-2 text-sm text-red-700">
          {start.error.message}
        </p>
      )}
    </div>
  );
}