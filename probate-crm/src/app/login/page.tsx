"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { signIn } from "@/app/(crm)/leads/actions";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const result = await signIn(String(form.get("email") || ""), String(form.get("password") || ""));
    if (result.error) {
      setError(result.error);
      setPending(false);
      return;
    }
    router.replace("/leads");
    router.refresh();
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 p-4">
      <form onSubmit={onSubmit} className="w-full max-w-md rounded-xl border border-line bg-white p-8 shadow-sm">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-primary text-white text-2xl">
            PG
          </div>
          <h1 className="text-2xl font-semibold">Probate CRM Pro</h1>
          <p className="mt-1 text-sm text-muted">Sign in to manage your probate leads</p>
        </div>
        <label className="mb-3 block text-sm font-medium">
          Email
          <input
            name="email"
            type="email"
            required
            autoComplete="email"
            placeholder="scott@probateguardians.com"
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
          />
        </label>
        <label className="mb-4 block text-sm font-medium">
          Password
          <input name="password" type="password" required autoComplete="current-password" className="mt-1 w-full rounded-md border border-line px-3 py-2" />
        </label>
        {error ? <p className="mb-3 text-sm text-red-600">{error}</p> : null}
        <button type="submit" disabled={pending} className="w-full rounded-md bg-primary px-4 py-2.5 font-medium text-white disabled:opacity-60">
          {pending ? "Signing in..." : "Sign In"}
        </button>
      </form>
    </div>
  );
}
