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
      if (url.includes("/providers")) {
        return json([{ value: "900123456", label: "Prestador de prueba" }]);
      }
      if (url.includes("/extraction/prepare")) {
        return json({
          status: "prepared",
          prepared_at: "2026-11-03T19:00:00Z",
          invoice_ids: ["ZmFrZQ"],
          transaction_ids: ["1001"],
          invoice_count: 1,
          transaction_count: 1,
          contracts: ["CNT-2026-9"],
          providers: ["900123456"],
        });
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
    expect((transactionCheckbox as HTMLInputElement).checked).toBe(true);

    expect(await screen.findByText("1 transacciones seleccionadas")).not.toBeNull();

    fireEvent.click(
      screen.getByRole("button", { name: "Confirmar selección" }),
    );

    expect(await screen.findByText("Selección preparada")).not.toBeNull();
    expect(screen.getByText(/La extracción aún no se ha iniciado/)).not.toBeNull();
  });
});


describe("filtros y selección global", () => {
  it("permite escribir un contrato y elegir una sugerencia con el teclado", async () => {
    mockApi();

    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter>
          <GenerationPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    const contractInput = screen.getByRole("combobox", { name: "Contrato" });
    fireEvent.focus(contractInput);
    fireEvent.change(contractInput, { target: { value: "CNT" } });

    const option = await screen.findByRole("option", { name: "CNT-2026-9" });
    expect(option).not.toBeNull();

    fireEvent.keyDown(contractInput, { key: "ArrowDown" });
    fireEvent.keyDown(contractInput, { key: "Enter" });

    expect((contractInput as HTMLInputElement).value).toBe("CNT-2026-9");
  });

  it("selecciona todas las facturas encontradas aunque no estén en la página visible", async () => {
    const invoices = Array.from({ length: 26 }, (_, index) => ({
      ...invoicePage.items[0],
      id: "invoice-" + (index + 1),
      invoice: "FE" + String(index + 1).padStart(3, "0"),
    }));
    const transactions = invoices.map((invoice, index) => ({
      id: String(2000 + index),
      invoice: invoice.invoice,
      contract: invoice.contract,
      nit_provider: invoice.nit_provider,
      provider_code: "12345",
      rips_date: "2026-08-12",
      filing_date: "2026-08-20",
    }));

    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: string | URL) => {
        const url = String(input);
        const json = (data: unknown) =>
          Promise.resolve(
            new Response(JSON.stringify(data), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            }),
          );

        if (url.includes("/contracts")) return json([]);
        if (url.includes("/providers")) return json([]);
        if (url.includes("/transactions/search")) {
          return json({
            items: transactions,
            total: transactions.length,
            page: 1,
            page_size: 100,
          });
        }
        if (url.includes("/invoices") && url.includes("page_size=100")) {
          return json({
            items: invoices,
            total: invoices.length,
            page: 1,
            page_size: 100,
            warnings: [],
          });
        }
        if (url.includes("/invoices")) {
          return json({
            items: invoices.slice(0, 25),
            total: invoices.length,
            page: 1,
            page_size: 25,
            warnings: [],
          });
        }
        return json({});
      }),
    );

    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter>
          <GenerationPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Buscar facturas" }));
    await screen.findByLabelText("Seleccionar factura FE001");

    fireEvent.click(screen.getByRole("button", { name: "Seleccionar todas" }));

    expect(await screen.findByText("26 seleccionadas")).not.toBeNull();
    expect(
      await screen.findByText("26 transacciones seleccionadas"),
    ).not.toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Quitar selección global" }));
    expect(await screen.findByText("0 transacciones seleccionadas")).not.toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Seleccionar todas las transacciones" }));
    expect(await screen.findByText("26 transacciones seleccionadas")).not.toBeNull();
  });
});
