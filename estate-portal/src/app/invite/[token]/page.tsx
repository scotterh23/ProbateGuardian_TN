"use client";

import { FormEvent, useState } from "react";
import { useParams } from "next/navigation";
import { BrandLogo } from "@/components/BrandLogo";

export default function InvitePage() {
  const { token } = useParams<{ token: string }>();
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
    window.location.href = "/dashboard";
  }

  return (
    <div className="min-h-screen bg-cream px-4 py-12">
      <div className="mx-auto mb-6 flex max-w-md justify-center">
        <BrandLogo href={null} size="hero" />
      </div>
      <div className="mx-auto max-w-md card p-6">
        <h1 className="font-serif text-2xl text-forest">Join this estate</h1>
        <p className="mt-2 mb-6 text-muted">
          Create your access so you can follow the property with the rest of the family.
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
            {pending ? "Saving…" : "Continue"}
          </button>
        </form>
      </div>
    </div>
  );
}
