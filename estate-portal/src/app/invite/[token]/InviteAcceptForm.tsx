"use client";

import { FormEvent, useState } from "react";
import { ROLE_LABEL } from "@/lib/status";

export function InviteAcceptForm({
  token,
  email,
  role,
  estate,
}: {
  token: string;
  email: string;
  role: keyof typeof ROLE_LABEL;
  estate: { id: string; nickname: string; address: string; city: string; county: string };
}) {
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError("");
    const form = new FormData(e.currentTarget);
    const res = await fetch("/api/auth/accept-invite", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({
        token,
        name: form.get("name"),
        password: form.get("password"),
      }),
    });
    const data = await res.json().catch(() => ({}));
    setPending(false);
    if (!res.ok) {
      setError(data.error || "Could not accept this invite.");
      return;
    }
    window.location.href = data.redirectTo || `/estates/${estate.id}`;
  }

  return (
    <div className="mx-auto max-w-md card p-6">
      <h1 className="font-serif text-2xl text-forest">Join this estate</h1>
      <p className="mt-2 text-muted">
        Create your access for <span className="font-semibold text-forest">{estate.nickname}</span>
        {" — "}
        {estate.address}, {estate.city} · {estate.county} County.
      </p>
      <p className="mt-2 mb-6 text-sm text-muted">
        Invited as <span className="font-semibold text-forest">{ROLE_LABEL[role]}</span> · {email}
      </p>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-semibold" htmlFor="name">
            Your name
          </label>
          <input id="name" name="name" required className="w-full rounded-xl border border-line px-3 py-3" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-semibold" htmlFor="password">
            Choose a password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            minLength={8}
            required
            className="w-full rounded-xl border border-line px-3 py-3"
          />
        </div>
        {error && <p className="text-sm text-red-700">{error}</p>}
        <button className="btn-primary w-full rounded-xl py-3" disabled={pending}>
          {pending ? "Saving…" : "Continue to this estate"}
        </button>
      </form>
    </div>
  );
}
