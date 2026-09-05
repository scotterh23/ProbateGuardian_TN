"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { applyAttorneyContactImport, previewAttorneyContactImport } from "@/app/(crm)/attorneys/actions";
import type { AttorneyImportSkip, AttorneyImportUpdate } from "@/lib/attorney-contact";

const SAMPLE = `attorney_id,firm,email,phone
016c5ae0-b0d2-4d71-a198-8acca7e8dec8,Example Firm,name@firm.com,6155550100`;

export function AttorneyImportForm() {
  const router = useRouter();
  const [csv, setCsv] = useState("");
  const [pending, start] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [updates, setUpdates] = useState<AttorneyImportUpdate[] | null>(null);
  const [skipped, setSkipped] = useState<AttorneyImportSkip[]>([]);
  const [result, setResult] = useState<string | null>(null);

  function runPreview() {
    setError(null);
    setResult(null);
    start(async () => {
      try {
        const preview = await previewAttorneyContactImport(csv);
        setUpdates(preview.updates);
        setSkipped(preview.skipped);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not preview");
      }
    });
  }

  function runApply() {
    setError(null);
    start(async () => {
      try {
        const applied = await applyAttorneyContactImport(csv);
        setResult(`Updated ${applied.updated} attorney row${applied.updated === 1 ? "" : "s"}. Leads were not touched.`);
        setUpdates(null);
        router.refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not apply import");
      }
    });
  }

  return (
    <div className="space-y-4">
      <label className="block space-y-1 text-sm">
        <span className="font-medium">Upload CSV</span>
        <input
          type="file"
          accept=".csv,text/csv,text/plain"
          className="block text-sm"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (!file) return;
            file.text().then((text) => {
              setCsv(text);
              setUpdates(null);
              setResult(null);
            });
          }}
        />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="font-medium">CSV or paste</span>
        <textarea
          value={csv}
          onChange={(e) => {
            setCsv(e.target.value);
            setUpdates(null);
            setResult(null);
          }}
          rows={8}
          spellCheck={false}
          placeholder={SAMPLE}
          className="w-full rounded-md border border-line bg-white p-3 font-mono text-xs"
        />
      </label>
      <p className="text-xs text-muted">
        Required column: <code>attorney_id</code>. Optional: firm, email, phone, county, address. Preview first —
        nothing is saved until you confirm.
      </p>
      <div className="flex flex-wrap gap-2">
        <button type="button" disabled={pending || !csv.trim()} onClick={runPreview} className="rounded-md bg-primary px-3 py-2 text-sm text-white disabled:opacity-60">
          {pending ? "Working…" : "Preview updates"}
        </button>
        {updates && updates.length > 0 ? (
          <button type="button" disabled={pending} onClick={runApply} className="rounded-md border border-line bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50">
            Commit {updates.length} update{updates.length === 1 ? "" : "s"}
          </button>
        ) : null}
      </div>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {result ? <p className="text-sm text-emerald-700">{result}</p> : null}
      {updates ? (
        <div className="rounded-xl border border-line bg-white p-4">
          <h2 className="font-semibold">{updates.length} attorney row{updates.length === 1 ? "" : "s"} will change</h2>
          {updates.length === 0 ? <p className="mt-2 text-sm text-muted">Nothing to write. Check skipped rows below.</p> : null}
          <div className="mt-3 space-y-3">
            {updates.map((row) => (
              <div key={`${row.id}-${row.changes.map((c) => c.field).join("-")}`} className="rounded-md border border-line p-3 text-sm">
                <p className="font-medium">{row.name}</p>
                <p className="text-xs text-muted">{row.id}</p>
                <ul className="mt-2 space-y-1">
                  {row.changes.map((change) => (
                    <li key={change.field}>
                      <span className="capitalize">{change.field}</span>: {change.from || "—"} → {change.to}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {skipped.length ? (
        <div className="rounded-xl border border-dashed border-line p-4 text-sm">
          <h2 className="font-semibold">{skipped.length} skipped</h2>
          <ul className="mt-2 space-y-1 text-muted">
            {skipped.slice(0, 40).map((row) => (
              <li key={`${row.line}-${row.attorney_id || "none"}`}>
                Line {row.line}
                {row.attorney_id ? ` · ${row.attorney_id}` : ""}: {row.reason}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
