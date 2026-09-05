export const dynamic = "force-dynamic";

import Link from "next/link";
import { loadAttorneys } from "@/lib/attorneys";

function cell(value: string | null) {
  return value?.trim() ? value : "—";
}

export default async function AttorneysPage() {
  const attorneys = await loadAttorneys();
  const missing = attorneys.filter((row) => !row.firm && !row.email && !row.phone).length;

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Attorneys</h1>
          <p className="text-sm text-muted">
            {attorneys.length} on the board · {missing} missing firm, email, and phone. TN Public Notice usually
            only gives names — add contact here or via CSV. Leads are not changed.
          </p>
        </div>
        <Link href="/attorneys/import" className="rounded-md border border-line bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50">
          Import contacts CSV
        </Link>
      </div>
      <div className="overflow-x-auto rounded-xl border border-line bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-muted">
            <tr>
              <th className="px-3 py-2 font-semibold">Name</th>
              <th className="px-3 py-2 font-semibold">Firm</th>
              <th className="px-3 py-2 font-semibold">Email</th>
              <th className="px-3 py-2 font-semibold">Phone</th>
              <th className="px-3 py-2 font-semibold">County</th>
            </tr>
          </thead>
          <tbody>
            {attorneys.map((row) => (
              <tr key={row.id} className="border-t border-line hover:bg-slate-50">
                <td className="px-3 py-2">
                  <Link href={`/attorneys/${row.id}`} className="font-medium text-primary hover:underline">
                    {row.full_name || "Unnamed attorney"}
                  </Link>
                </td>
                <td className="px-3 py-2 text-slate-700">{cell(row.firm)}</td>
                <td className="px-3 py-2 text-slate-700">{cell(row.email)}</td>
                <td className="px-3 py-2 text-slate-700">{cell(row.phone)}</td>
                <td className="px-3 py-2 text-slate-700">{cell(row.county)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
