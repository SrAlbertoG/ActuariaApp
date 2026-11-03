import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LoginPage } from "./LoginPage";
import { SessionGate } from "./SessionGate";

const DISCONNECTED = {
  connected: false, server: null, database: null, username: null,
  auth_type: null, has_saved_credentials: false, saved_profile: null,
};
const LOCAL_ACCOUNT = {
  available: true, account: "PC-01\\analista", domain_joined: false,
  message: "Este equipo no parece estar unido a un dominio.",
};

/** Simula el backend; `loginError` define cómo responde /login. */
function mockBackend(loginError: { code: string; message: string }) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((url: string) => {
      const json = (body: unknown, status = 200) =>
        Promise.resolve(new Response(JSON.stringify(body), { status }));
      if (url.endsWith("/login")) return json({ error: loginError }, 401);
      if (url.endsWith("/windows-info")) return json(LOCAL_ACCOUNT);
      return json(DISCONNECTED);
    }),
  );
}

function renderLogin() {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <SessionGate><LoginPage /></SessionGate>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("LoginPage", () => {
  it("con Windows oculta usuario y contraseña y muestra la cuenta y el aviso", async () => {
    mockBackend({ code: "x", message: "x" });
    renderLogin();
    await screen.findByLabelText("Servidor");

    fireEvent.change(screen.getByLabelText("Tipo de autenticación"), { target: { value: "windows" } });
    expect(screen.queryByLabelText("Contraseña")).toBeNull();
    expect(await screen.findByText("PC-01\\analista")).not.toBeNull();
    expect(screen.getByText(/no parece estar unido a un dominio/)).not.toBeNull();
  });

  it("muestra el mensaje cuando las credenciales SQL son incorrectas", async () => {
    mockBackend({ code: "invalid_credentials", message: "Usuario o contraseña incorrectos." });
    renderLogin();
    await screen.findByLabelText("Servidor");

    fireEvent.change(screen.getByLabelText("Servidor"), { target: { value: "srv" } });
    fireEvent.change(screen.getByLabelText("Usuario"), { target: { value: "analista" } });
    fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "mala" } });
    fireEvent.click(screen.getByRole("button", { name: "Conectar" }));

    expect(await screen.findByText("Usuario o contraseña incorrectos.")).not.toBeNull();
  });

  it("si Windows es rechazado ofrece pasar a usuario y contraseña", async () => {
    mockBackend({ code: "windows_auth_failed", message: "El servidor rechazó tu cuenta de Windows." });
    renderLogin();
    await screen.findByLabelText("Servidor");

    fireEvent.change(screen.getByLabelText("Tipo de autenticación"), { target: { value: "windows" } });
    // El servidor es obligatorio: sin él el formulario no se envía.
    fireEvent.change(screen.getByLabelText("Servidor"), { target: { value: "srv" } });
    fireEvent.click(screen.getByRole("button", { name: "Conectar" }));
    expect(await screen.findByText("El servidor rechazó tu cuenta de Windows.")).not.toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Ingresar con usuario y contraseña" }));
    expect(await screen.findByLabelText("Contraseña")).not.toBeNull();
    expect(screen.queryByText("El servidor rechazó tu cuenta de Windows.")).toBeNull();
  });
});