import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

interface ThemeContextValue {
  isDark: boolean;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function getInitialTheme(): boolean {
  try {
    return window.localStorage.getItem("actuaria-theme") === "dark";
  } catch {
    return false;
  }
}

/** Mantiene el tema de toda la aplicación y recuerda la preferencia local. */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [isDark, setIsDark] = useState(getInitialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
    document.documentElement.style.colorScheme = isDark ? "dark" : "light";

    try {
      window.localStorage.setItem("actuaria-theme", isDark ? "dark" : "light");
    } catch {
      // La interfaz sigue funcionando aunque el almacenamiento esté bloqueado.
    }
  }, [isDark]);

  const toggleTheme = () => setIsDark((current) => !current);

  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const value = useContext(ThemeContext);
  if (!value) {
    throw new Error("useTheme debe utilizarse dentro de ThemeProvider.");
  }
  return value;
}
