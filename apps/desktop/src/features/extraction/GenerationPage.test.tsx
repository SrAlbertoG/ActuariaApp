import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GenerationPage } from "./GenerationPage";

const invoicePage = {
  items: [
    {
      id: "ZmFrZQ",
      invoice: "FE001",
      nit_provider: "900123456",
      provider_name: "Prestador de prueba",
      contract: "CNT-2026-9",
      service_month: "2026-08",
      invoice_date: null,
      filing_date: null,
      billed_amount: "125000",
      source: "base_fixed",
    },
  ],
  total: 1,
  page: 1,
  page_size: 25,
  warnings: [],
};

const transactionPage = {
  items: [
    {
      id: "1001",
      invoice: "FE001",
      contract: "CNT-2026-9",
      nit_provider: "900123456",
      provider_code: "12345",
      rips_date: "2026-08-12",
      filing_date: "2026-08-20",
    },
  ],
  total: 1,
  page: 1,
  page_size: 25,
};

function mockApi() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((url: string) => {
      const json = (data: unknown) =>
        Promise.resolve(
          new Response(JSON.stringify(data), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );

      if (url.includes("/contracts")) {
        return json([{ value: "CNT-2026-9", label: "CNT-2026-9" }]);
      }
      if (url.includes("/transactions/search")) return json(transactionPage);
      if (url.includes("/invoices/")) return json(invoicePage.items[0]);
      if (url.includes("/invoices")) return json(invoicePage);
      return json({});
    }),
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("GenerationPage", () => {
  it("permite buscar facturas, consultar transacciones y preparar selección", async () => {
    mockApi();

    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter>
          <GenerationPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Buscar facturas" }));

    const invoiceCheckbox = await screen.findByLabelText(
      "Seleccionar factura FE001",
    );
    fireEvent.click(invoiceCheckbox);

    const transactionCheckbox = await screen.findByLabelText(
      "Seleccionar transacción 1001",
    );
    fireEvent.click(transactionCheckbox);

    expect(screen.getByText("1 transacciones seleccionadas")).not.toBeNull();

    fireEvent.click(
      screen.getByRole("button", { name: "Confirmar selección" }),
    );

    expect(await screen.findByText("Selección preparada")).not.toBeNull();
    expect(screen.getByText(/La extracción aún no se ha iniciado/)).not.toBeNull();
  });
});
