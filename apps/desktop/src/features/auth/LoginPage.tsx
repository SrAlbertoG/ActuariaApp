import { useState, type FormEvent } from "react";
import { config } from "../../lib/config";
import type { AuthType } from "./types";
import {
  useForgetCredentials,
  useLogin,
  useSession,
  useWindowsInfo,
  type SessionState,
} from "./useSession";

const inputClass =
  "w-full rounded border border-slate-300 px-3 py-2 focus:border-blue-500 focus:outline-none";

/**
 * Formulario de acceso. Se rellena con el perfil guardado (sin contraseña)
 * cuando existe, para que tras un fallo de reconexión el usuario solo
 * corrija lo necesario.
 */
function LoginForm({ session }: { session: SessionState }) {
  const { refetch, isFetching } = useSession();
  const login = useLogin();
  const forget = useForgetCredentials();
  const saved = session.status.saved_profile;

  const [authType, setAuthType] = useState<AuthType>(saved?.auth_type ?? "sql");
  const [server, setServer] = useState(saved?.server ?? config.defaultServer);
  const [database, setDatabase] = useState(saved?.database ?? config.defaultDatabase);
  const [username, setUsername] = useState(saved?.username ?? "");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);

  const usesSql = authType === "sql";
  const windowsInfo = useWindowsInfo(!usesSql).data;

  /** Cambiar de modo descarta el error anterior: pertenece al otro modo. */
  const changeAuthType = (value: AuthType) => {
    login.reset();
    setAuthType(value);
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    login.mutate(
      {
        payload: {
          server,
          database: database || null,
          auth_type: authType,
          username: usesSql ? username : null,
          password: usesSql ? password : null,
        },
        remember,
      },
      // Por seguridad, la contraseña se borra del formulario si el acceso falla.
      { onError: () => setPassword("") },
    );
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-6">
      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-4 rounded-lg bg-white p-8 shadow">
        <div>
          <h1 className="text-xl font-semibold text-slate-800">Plataforma de Actuaría</h1>
          <p className="text-sm text-slate-500">Conéctate a SQL Server para continuar.</p>
        </div>

        {session.autoLoginError && (
          <div role="status" className="space-y-2 rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
            <p>No se pudo reconectar automáticamente: {session.autoLoginError.message}</p>
            <div className="flex gap-3">
              <button type="button" onClick={() => refetch()} disabled={isFetching} className="font-medium underline disabled:opacity-50">
                Reintentar reconexión
              </button>
              <button type="button" onClick={() => forget.mutate()} disabled={forget.isPending} className="font-medium underline disabled:opacity-50">
                Olvidar credenciales guardadas
              </button>
            </div>
          </div>
        )}

        <div>
          <label htmlFor="authType" className="mb-1 block text-sm font-medium text-slate-700">Tipo de autenticación</label>
          <select id="authType" value={authType} onChange={(e) => changeAuthType(e.target.value as AuthType)} className={inputClass}>
            <option value="sql">Usuario y contraseña de SQL Server</option>
            <option value="windows">Autenticación de Windows</option>
          </select>
        </div>

        <div>
          <label htmlFor="server" className="mb-1 block text-sm font-medium text-slate-700">Servidor</label>
          <input id="server" required value={server} onChange={(e) => setServer(e.target.value)} className={inputClass} />
        </div>

        <div>
          <label htmlFor="database" className="mb-1 block text-sm font-medium text-slate-700">Base de datos</label>
          <input id="database" value={database} onChange={(e) => setDatabase(e.target.value)} className={inputClass} />
        </div>

        {usesSql ? (
          <>
            <div>
              <label htmlFor="username" className="mb-1 block text-sm font-medium text-slate-700">Usuario</label>
              <input id="username" required autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} className={inputClass} />
            </div>
            <div>
              <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">Contraseña</label>
              <input id="password" type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} className={inputClass} />
            </div>
          </>
        ) : (
          <div className="space-y-2 rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
            <p>
              Se usará la cuenta de Windows con la que iniciaste sesión en este equipo
              {windowsInfo?.account ? <>: <strong>{windowsInfo.account}</strong></> : null}.
              No necesitas escribir usuario ni contraseña.
            </p>
            {windowsInfo?.message && <p className="text-amber-800">{windowsInfo.message}</p>}
          </div>
        )}

        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
          {usesSql
            ? "Recordar mis credenciales en este equipo"
            : "Recordar servidor y base de datos (no se guarda ninguna contraseña)"}
        </label>

        {login.error && (
          <div role="alert" className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">
            <p>{login.error.message}</p>
            {login.error.code === "windows_auth_failed" && (
              <button type="button" onClick={() => changeAuthType("sql")} className="mt-2 font-medium underline">
                Ingresar con usuario y contraseña
              </button>
            )}
          </div>
        )}

        <button type="submit" disabled={login.isPending} className="w-full rounded bg-blue-600 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50">
          {login.isPending ? "Conectando…" : "Conectar"}
        </button>
      </form>
    </div>
  );
}

/** Página de acceso. SessionGate garantiza que la sesión ya está cargada. */
export function LoginPage() {
  const { data } = useSession();
  if (!data) return null;
  return <LoginForm session={data} />;
}