import "./globals.css";
import type { Metadata } from "next";
import { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Leaf AI",
  description: "Flujo de caja, inventario y campañas para comercios",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body className="bg-neutral-50 text-neutral-900">
        <div className="flex min-h-screen">
          <aside className="w-64 border-r bg-white">
            <div className="p-4 text-lg font-semibold">Leaf AI</div>
            <nav className="px-2 text-sm">
              <a className="block rounded px-3 py-2 hover:bg-neutral-100" href="/panel">📊 Panel</a>
              <a className="block rounded px-3 py-2 hover:bg-neutral-100" href="/inventario">📦 Inventario</a>
              <a className="block rounded px-3 py-2 hover:bg-neutral-100" href="/campanas">📣 Campañas</a>
            </nav>
          </aside>
          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}
