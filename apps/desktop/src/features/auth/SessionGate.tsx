import type { ReactNode } from "react";
import { useSession } from "./useSession";

function Centered({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-6">
      {children}
    </div>
  );
}

/**
 * Puerta de arranque: no muestra la aplicación hasta saber el estado de la
 * sesión. Durante ese tiempo se está reconectando con las credenciales
 * guardadas (si las hay).
 */
export function SessionGate({ children }: { children: ReactNode }) {
  const { isPending, isError, error, refetch, isFetching } = useSession();

  if (isPending) {
    return (
      <Centered>
        <p className="text-slate-600">Verificando conexión con SQL Server…</p>
      </Centered>
    );
  }

  if (isError) {
    return (
      <Centered>
        <div className="max-w-md rounded-lg bg-white p-6 text-center shadow">
          <h1 className="mb-2 text-lg font-semibold text-slate-800">
            No se pudo iniciar la aplicación
          </h1>
          <p role="alert" className="mb-4 text-slate-600">{error.message}</p>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            Reintentar
          </button>
        </div>
      </Centered>
    );
  }

  return <>{children}</>;
}