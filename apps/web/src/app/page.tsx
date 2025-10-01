// apps/web/src/app/panel/page.tsx
import { getJSON } from "@/app/lib/api";
import { LineSeries, BarSeries } from "@/components/Charts";

type KPI = {
  ingresos_neto: number;
  cogs_neto: number;
  margen_bruto: number;
  gastos_neto: number;
  beneficio_neto: number;
};

type SalesPoint = {
  date: string;        // ISO date or yyyy-mm-dd
  ingresos: number;    // net revenue for the day
  cogs: number;        // cost of goods sold
  margen: number;      // ingresos - cogs
};

type ReorderItem = {
  product_id: string;
  name: string;
  demand_h: number;
  stock_on_hand: number;
  lead_time_days: number;
  safety_stock: number;
  reorder_qty: number;
};

function fmtCurrency(n: number, locale = "es-ES", currency = "EUR") {
  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(n);
  } catch {
    // fallback safe formatting if locale/currency not available
    return `${n.toFixed(0)} ${currency}`;
  }
}

export default async function Panel() {
  // 1) KPIs
  const kpi = await getJSON<KPI>("/api/sales/kpi");

  // 2) Ventas serie (últimos 30 días). Si aún no tienes este endpoint, devuelve [] y mostramos placeholder.
  const series =
    (await getJSON<SalesPoint[]>("/api/sales/series?days=30").catch(() => [])) ??
    [];

  // 3) Reposición inventario (h = 14 días)
  const reorder =
    (await getJSON<ReorderItem[]>("/api/inventory/reorder?h=14").catch(
      () => []
    )) ?? [];

  const cards: Array<[string, number]> = [
    ["Ingresos neto", kpi.ingresos_neto ?? 0],
    ["Coste de ventas (COGS)", kpi.cogs_neto ?? 0],
    ["Margen bruto", kpi.margen_bruto ?? 0],
    ["Gastos neto", kpi.gastos_neto ?? 0],
    ["Beneficio neto", kpi.beneficio_neto ?? 0],
  ];

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-2xl font-semibold">Panel — Flujo de ventas</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-4">
        {cards.map(([t, v]) => (
          <div
            key={t}
            className="rounded-xl border bg-white p-4 shadow-sm flex flex-col"
          >
            <span className="text-xs text-neutral-500">{t}</span>
            <span className="mt-2 text-xl font-semibold">
              {fmtCurrency(v)}
            </span>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Ventas vs COGS vs Margen */}
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              Ventas / COGS / Margen — últimos 30 días
            </h2>
          </div>

          {series.length > 0 ? (
            <LineSeries
              data={series}
              lines={[
                { dataKey: "ingresos", name: "Ingresos" },
                { dataKey: "cogs", name: "COGS" },
                { dataKey: "margen", name: "Margen" },
              ]}
            />
          ) : (
            <div className="text-sm text-neutral-500">
              No hay datos de serie disponibles todavía.
            </div>
          )}
        </div>

        {/* Reponer stock (si aplica) */}
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Productos a reponer (14d)</h2>
          </div>

          {reorder.length > 0 ? (
            <BarSeries
              data={reorder.map((r) => ({
                name: r.name ?? r.product_id,
                reorder_qty: r.reorder_qty,
              }))}
              dataKey="reorder_qty"
              name="Unidades"
            />
          ) : (
            <div className="text-sm text-neutral-500">
              No se recomienda reponer ningún producto en este horizonte.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
