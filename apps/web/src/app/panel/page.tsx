import { getJSON } from "@/lib/api";

type KPI = {
  ingresos_neto: number;
  cogs_neto: number;
  margen_bruto: number;
  gastos_neto: number;
  beneficio_neto: number;
};

export default async function Panel() {
  const kpi = await getJSON<KPI>("/api/sales/kpi");
  const fmt = (n: number) =>
    n.toLocaleString("es-ES", { style: "currency", currency: "EUR" });

  const cards: [string, number][] = [
    ["Ingresos (neto)", kpi.ingresos_neto],
    ["Coste de ventas", kpi.cogs_neto],
    ["Margen bruto", kpi.margen_bruto],
    ["Gastos (neto)", kpi.gastos_neto],
    ["Beneficio neto", kpi.beneficio_neto],
  ];

  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-semibold">
        📊 Panel — Flujo de caja y ventas
      </h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
        {cards.map(([t, v]) => (
          <div key={t} className="rounded-lg border bg-white p-4">
            <div className="text-xs text-neutral-500">{t}</div>
            <div className="mt-1 text-lg font-semibold">{fmt(v)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
