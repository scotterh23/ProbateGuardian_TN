import { ROLE_LABEL } from "@/lib/status";

export function InviteAcceptForm({
  token,
  email,
  role,
  estate,
  error,
}: {
  token: string;
  email: string;
  role: keyof typeof ROLE_LABEL;
  estate: { id: string; nickname: string; address: string; city: string; county: string };
  error?: string;
}) {
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
    </div>
  );
}
