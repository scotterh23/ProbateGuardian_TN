"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { updateAttorneyContact } from "@/app/(crm)/attorneys/actions";
import { ATTORNEY_CONTACT_FIELDS, type AttorneyContactField } from "@/lib/attorney-contact";
import type { Attorney } from "@/lib/types";

const LABELS: Record<AttorneyContactField, string> = {
  firm: "Firm",
  email: "Email",
  phone: "Phone",
  county: "County",
  address: "Address",
};

export function AttorneyContactForm({ attorney }: { attorney: Attorney }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  return (
    <form
      className="space-y-4 rounded-xl border border-line bg-white p-5"
      onSubmit={(event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        const incoming: Partial<Record<AttorneyContactField, string>> = {};
        const clear: Partial<Record<AttorneyContactField, boolean>> = {};
        for (const field of ATTORNEY_CONTACT_FIELDS) {
          incoming[field] = String(form.get(field) || "");
          clear[field] = form.get(`clear_${field}`) === "on";
        }
        setError(null);
        setSaved(false);
        start(async () => {
          try {
            await updateAttorneyContact(attorney.id, incoming, clear);
            setSaved(true);
            router.refresh();
          } catch (err) {
            setError(err instanceof Error ? err.message : "Could not save attorney");
          }
        });
      }}
    >
      <p className="text-sm text-muted">
        Blank fields are left unchanged. Check <strong>Clear</strong> only if you want to wipe a value that is
        already on file.
      </p>
      <div className="grid gap-4 sm:grid-cols-2">
        {ATTORNEY_CONTACT_FIELDS.map((field) => (
          <label key={field} className="space-y-1 text-sm">
            <span className="flex items-center justify-between font-medium">
              {LABELS[field]}
              {attorney[field] ? (
                <span className="flex items-center gap-1 font-normal text-xs text-muted">
                  <input type="checkbox" name={`clear_${field}`} className="rounded border-line" />
                  Clear
                </span>
              ) : null}
            </span>
            <input
              name={field}
              type={field === "email" ? "email" : "text"}
              defaultValue={attorney[field] ?? ""}
              placeholder="Leave blank to keep current"
              className="w-full rounded-md border border-line px-3 py-2"
            />
          </label>
        ))}
      </div>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {saved ? <p className="text-sm text-emerald-700">Saved. Firm, email, and phone now show on the board.</p> : null}
      <button type="submit" disabled={pending} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
        {pending ? "Saving…" : "Save contact"}
      </button>
    </form>
  );
}
