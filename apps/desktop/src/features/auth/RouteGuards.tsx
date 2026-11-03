import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useSession } from "./useSession";

/**
 * Protege los módulos: sin conexión activa a SQL Server redirige al acceso.
 * Es el equivalente en la interfaz de `require_sql_connection` del backend.
 */
export function RequireConnection({ children }: { children: ReactNode }) {
  const { data } = useSession();
  if (!data?.status.connected) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

/** Si ya hay sesión, la pantalla de acceso no tiene sentido: va al inicio. */
export function RedirectIfConnected({ children }: { children: ReactNode }) {
  const { data } = useSession();
  if (data?.status.connected) return <Navigate to="/" replace />;
  return <>{children}</>;
}