"use client";

import { useEffect, useState } from "react";
import { BrandLogo } from "@/components/BrandLogo";
import { ROLE_LABEL } from "@/lib/status";

type InviteDetails = {
  email: string;
  role: keyof typeof ROLE_LABEL;
  used: boolean;
  expired: boolean;
  estate: { id: string; nickname: string; address: string; city: string; county: string };
};

export function InviteClient({ token, error }: { token: string; error?: string }) {
  const [details, setDetails] = useState<InviteDetails | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const res = await fetch(`/api/invites/${encodeURIComponent(token)}`, {
        credentials: "same-origin",
        cache: "no-store",
      });
      const data = await res.json().catch(() => ({}));
      if (cancelled) return;
      setLoading(false);
      if (!res.ok) {
        setLoadError(data.error || "This invite is not valid.");
        return;
      }
      setDetails(data);
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <div className="min-h-screen bg-cream px-4 py-12">
      <div className="mx-auto mb-6 flex max-w-md justify-center">
        <BrandLogo href={null} size="hero" />
      </div>
      <div className="mx-auto max-w-md card p-6">
        {loading ? (
          <p className="text-muted">Opening your invite…</p>
        ) : details?.used ? (
          <InviteMessage
            title="This invite was already used"
            body="If you already created your access, sign in to open the estate."
            href={`/login?next=${encodeURIComponent(`/estates/${details.estate.id}`)}`}
            action="Sign in to this estate"
          />
        ) : details?.expired ? (
          <InviteMessage
            title="This invite has expired"
            body="Ask Probate Guardians to send a fresh link. Invites are good for 14 days."
          />
        ) : loadError && !details ? (
          <InviteMessage title="This invite is not valid" body={loadError} />
        ) : (
          <AcceptForm token={token} details={details} error={error} />
        )}
      </div>
    </div>
  );
}

function AcceptForm({
  token,
  details,
  error,
}: {
  token: string;
  details: InviteDetails | null;
  error?: string;
}) {
  return (
    <>
      <h1 className="font-serif text-2xl text-forest">Join this estate</h1>
      {details ? (
        <>
          <p className="mt-2 text-muted">
            Create your access for{" "}
            <span className="font-semibold text-forest">{details.estate.nickname}</span>
            {" — "}
            {details.estate.address}, {details.estate.city} · {details.estate.county} County.
          </p>
          <p className="mt-2 mb-6 text-sm text-muted">
            Invited as{" "}
            <span className="font-semibold text-forest">{ROLE_LABEL[details.role]}</span> ·{" "}
            {details.email}
          </p>
        </>
      ) : (
        <p className="mt-2 mb-6 text-muted">
          Create your name and password to open this estate.
        </p>
      )}
      <form action="/api/auth/accept-invite" method="post" className="space-y-4">
        <input type="hidden" name="token" value={token} />
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
        <button className="btn-primary w-full rounded-xl py-3">Continue to this estate</button>
      </form>
    </>
  );
}

function InviteMessage({
  title,
  body,
  href,
  action,
}: {
  title: string;
  body: string;
  href?: string;
  action?: string;
}) {
  return (
    <>
      <h1 className="font-serif text-2xl text-forest">{title}</h1>
      <p className="mt-2 text-muted">{body}</p>
      {href && action ? (
        <a href={href} className="btn-primary mt-6 inline-flex rounded-xl px-4 py-3">
          {action}
        </a>
      ) : null}
    </>
  );
}
