import { afterEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "./api";

afterEach(() => vi.unstubAllGlobals());

describe("apiFetch", () => {
  it("devuelve el JSON y envía el token de sesión", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ pong: true })));
    vi.stubGlobal("fetch", fetchMock);

    expect(await apiFetch("/ping")).toEqual({ pong: true });
    const headers = fetchMock.mock.calls[0][1].headers;
    expect(headers["X-Session-Token"]).toBeDefined();
  });

  it("convierte el error uniforme del backend en ApiError", async () => {
    const body = { error: { code: "invalid_credentials", message: "Usuario o contraseña incorrectos." } };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status: 401 })));

    await expect(apiFetch("/x")).rejects.toMatchObject({ code: "invalid_credentials", status: 401 });
  });

  it("informa backend_unreachable cuando no hay conexión", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(apiFetch("/x")).rejects.toMatchObject({ code: "backend_unreachable" });
  });
});