import { Link } from "react-router-dom";

import {
  useForgetCredentials,
  useLogout,
  useSession,
} from "../auth/useSession";

const MODULES = [
  {
    name: "Facturas y transacciones",
    description:
      "Consulta facturas, revisa transacciones RIPS y prepara la selección para extracción.",
    note: "Entregable 2",
    path: "/generation",
    available: true,
  },
  {
    name: "Extracción de datos",
    description:
      "Extracción de consultas, procedimientos, medicamentos e insumos, sin homologación.",
    note: "Entregable 3",
    path: null,
    available: false,
  },
];

/** Pantalla inicial, accesible únicamente con conexión activa. */
export function HomePage() {
  const { data } = useSession();
  const logout = useLogout();
  const forget = useForgetCredentials();

  if (!data) return null;
  const session = data.status;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-blue-600">
              ActuariaApp
            </p>
            <h1 className="text-xl font-semibold text-slate-900">
              Plataforma de Actuaría
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Conectado a {session.server}
              {session.database ? " · " + session.database : ""}
              {session.username ? " · " + session.username : ""}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {session.has_saved_credentials && (
              <button
                type="button"
                onClick={() => forget.mutate()}
                disabled={forget.isPending}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
              >
                {forget.isPending
                  ? "Eliminando…"
                  : "Olvidar credenciales guardadas"}
              </button>
            )}
            <button
              type="button"
              onClick={() => logout.mutate()}
              disabled={logout.isPending}
              className="rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
            >
              {logout.isPending ? "Cerrando…" : "Cerrar sesión"}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-slate-900">
            Módulos de trabajo
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Selecciona el proceso que deseas realizar.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {MODULES.map((module) => {
            const content = (
              <>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl text-blue-700">
                    {module.available ? "▤" : "⚙"}
                  </div>
                  <span
                    className={
                      "rounded-full px-3 py-1 text-xs font-semibold " +
                      (module.available
                        ? "bg-emerald-50 text-emerald-700"
                        : "bg-slate-100 text-slate-500")
                    }
                  >
                    {module.available ? "Disponible" : "Próximamente"}
                  </span>
                </div>
                <div className="mt-5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">
                    {module.note}
                  </p>
                  <h3 className="mt-1 text-lg font-semibold text-slate-900">
                    {module.name}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-slate-500">
                    {module.description}
                  </p>
                </div>
                <div className="mt-6 text-sm font-semibold text-blue-700">
                  {module.available ? "Abrir módulo →" : "No disponible todavía"}
                </div>
              </>
            );

            return module.available && module.path ? (
              <Link
                key={module.name}
                to={module.path}
                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md"
              >
                {content}
              </Link>
            ) : (
              <div
                key={module.name}
                aria-disabled="true"
                className="rounded-2xl border border-slate-200 bg-white p-6 opacity-70"
              >
                {content}
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
