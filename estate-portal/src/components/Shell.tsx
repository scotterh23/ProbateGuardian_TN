import Link from "next/link";
import { SessionUser } from "@/lib/auth";
import { ROLE_LABEL } from "@/lib/status";

export function Shell({
  user,
  children,
}: {
  user: SessionUser;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-line bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Link href="/dashboard" className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-navy text-sm font-semibold text-white">
              PG
            </span>
            <span>
              <span className="block font-serif text-base leading-tight text-navy">
                Probate Guardians
              </span>
              <span className="block text-xs tracking-wide text-muted">
                Estate Portal
              </span>
            </span>
          </Link>
          <nav className="flex items-center gap-2 text-sm">
            <Link className="rounded-lg px-3 py-2 text-navy hover:bg-mist" href="/dashboard">
              Estates
            </Link>
            {user.role === "ADMIN" && (
              <Link className="rounded-lg px-3 py-2 text-navy hover:bg-mist" href="/admin">
                Admin
              </Link>
            )}
            <form action="/api/auth/logout" method="post">
              <button className="rounded-lg px-3 py-2 text-muted hover:bg-mist" type="submit">
                Sign out
              </button>
            </form>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
      <footer className="mx-auto max-w-6xl px-4 pb-10 text-sm text-muted">
        Signed in as {user.name} · {ROLE_LABEL[user.role]} · Not legal advice. Property
        coordination only.
      </footer>
    </div>
  );
}
