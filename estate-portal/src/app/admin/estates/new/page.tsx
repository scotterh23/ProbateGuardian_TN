"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function NewEstatePage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    const form = new FormData(e.currentTarget);
    const res = await fetch("/api/estates", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nickname: form.get("nickname"),
        address: form.get("address"),
        city: form.get("city"),
        county: form.get("county"),
        status: form.get("status"),
      }),
    });
    const data = await res.json();
    setPending(false);
    if (!res.ok) {
      setError(data.error || "Could not create estate.");
      return;
    }
    router.push(`/estates/${data.estate.id}`);
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-10">
      <Link href="/admin" className="text-sm text-muted">
        ← Admin
      </Link>
      <h1 className="mt-4 font-serif text-3xl text-forest">Create an estate</h1>
      <p className="mt-2 mb-6 text-muted">
        Start with the property. Then open the estate and invite the executor, heirs, and attorney.
      </p>
      <form onSubmit={onSubmit} className="card space-y-4 p-5">
        <Field name="nickname" label="Nickname" placeholder="Whitfield family home" />
        <Field name="address" label="Street address" placeholder="4521 Main St" />
        <Field name="city" label="City" placeholder="Lebanon" />
        <Field name="county" label="County" placeholder="Wilson" />
        <label className="block text-sm font-semibold">
          Starting status
          <select name="status" className="mt-1 w-full rounded-xl border border-line px-3 py-3 font-normal">
            <option value="LETTERS">Letters issued</option>
            <option value="VALUATION">Valuation</option>
            <option value="LISTED">Listed</option>
            <option value="UNDER_CONTRACT">Under contract</option>
            <option value="CLOSED">Closed</option>
          </select>
        </label>
        {error && <p className="text-sm text-red-700">{error}</p>}
        <button className="btn-primary w-full rounded-xl py-3" disabled={pending}>
          {pending ? "Saving…" : "Create estate"}
        </button>
      </form>
    </div>
  );
}

function Field({
  name,
  label,
  placeholder,
}: {
  name: string;
  label: string;
  placeholder: string;
}) {
  return (
    <label className="block text-sm font-semibold">
      {label}
      <input
        name={name}
        required
        placeholder={placeholder}
        className="mt-1 w-full rounded-xl border border-line px-3 py-3 font-normal"
      />
    </label>
  );
}
