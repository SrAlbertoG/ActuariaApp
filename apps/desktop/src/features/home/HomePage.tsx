import { useForgetCredentials, useLogout, useSession } from "../auth/useSession";

const MODULES = [
  { name: "Facturas y transacciones", note: "Entregable 2" },
  { name: "Extracción de datos", note: "Entregable 3" },
];

/** Pantalla inicial, accesible solo con conexión activa. */
export function HomePage() {
  const { data } = useSession();
  const logout = useLogout();
  const forget = useForgetCredentials();
  if (!data) return null;
  const s = data.status;

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="flex items-center justify-between bg-white px-6 py-3 shadow">
        <div>
          <p className="font-semibold text-slate-800">Plataforma de Actuaría</p>
          <p className="text-sm text-slate-500">
            Conectado a {s.server}
            {s.database ? ` · ${s.database}` : ""}
            {s.username ? ` · ${s.username}` : ""}
          </p>
        </div>
        <div className="flex gap-2">
          {s.has_saved_credentials && (
            <button onClick={() => forget.mutate()} disabled={forget.isPending} className="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50 disabled:opacity-50">
              Olvidar credenciales guardadas
            </button>
          )}
          <button onClick={() => logout.mutate()} disabled={logout.isPending} className="rounded bg-slate-800 px-3 py-1 text-sm text-white hover:bg-slate-700 disabled:opacity-50">
            Cerrar sesión
          </button>
        </div>
      </header>

      <main className="grid gap-4 p-6 sm:grid-cols-2">
        {MODULES.map((m) => (
          <div key={m.name} className="rounded-lg border border-dashed border-slate-300 bg-white p-6 opacity-70">
            <h2 className="font-medium text-slate-800">{m.name}</h2>
            <p className="text-sm text-slate-500">Disponible en el {m.note}</p>
          </div>
        ))}
      </main>
    </div>
  );
}