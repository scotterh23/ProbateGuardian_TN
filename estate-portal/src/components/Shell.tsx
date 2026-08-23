import Link from "next/link";
import { SessionUser } from "@/lib/auth";
import { ROLE_LABEL } from "@/lib/status";
import { BrandLogo } from "@/components/BrandLogo";

export function Shell({
  user,
  children,
}: {
  user: SessionUser;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-cream">
      <header className="sticky top-0 z-20 border-b border-line bg-warm-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <BrandLogo href="/dashboard" />
          <nav className="flex items-center gap-2 text-sm">
            <Link className="rounded-lg px-3 py-2 text-forest hover:bg-mist" href="/dashboard">
              Estates
            </Link>
            {user.role === "ADMIN" && (
              <Link className="rounded-lg px-3 py-2 text-forest hover:bg-mist" href="/admin">
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
