import Link from "next/link";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { Shell } from "@/components/Shell";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate } from "@/lib/status";

export default async function DashboardPage() {
  const session = await getSession();
  if (!session) redirect("/login");

  const estates =
    session.role === "ADMIN"
      ? await prisma.estate.findMany({
          orderBy: { updatedAt: "desc" },
          include: { updates: { orderBy: { createdAt: "desc" }, take: 1 } },
        })
      : (
          await prisma.estateMember.findMany({
            where: { userId: session.id },
            include: {
              estate: { include: { updates: { orderBy: { createdAt: "desc" }, take: 1 } } },
            },
            orderBy: { createdAt: "desc" },
          })
        ).map((m) => m.estate);

  const heading =
    session.role === "ATTORNEY"
      ? "Estates shared with your office"
      : session.role === "HEIR"
        ? "Family estates"
        : "Your estates";

  return (
    <Shell user={session}>
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-muted">Dashboard</p>
          <h1 className="font-serif text-3xl text-navy">{heading}</h1>
          <p className="mt-1 max-w-xl text-muted">
            Status and the latest update are the two things that matter most. Open an estate to see
            the full timeline, documents, and conversation.
          </p>
        </div>
        {session.role === "ADMIN" && (
          <Link href="/admin/estates/new" className="rounded-xl bg-navy px-4 py-3 font-semibold text-white">
            New estate
          </Link>
        )}
      </div>

      {estates.length === 0 ? (
        <div className="card p-8 text-muted">
          No estates yet. If you expected to see one, ask Probate Guardians to send an invite.
        </div>
      ) : (
        <ul className="grid gap-4">
          {estates.map((estate) => (
            <li key={estate.id}>
              <Link
                href={`/estates/${estate.id}`}
                className="card block p-5 transition hover:border-navy/30"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="font-serif text-xl text-navy">{estate.nickname}</h2>
                    <p className="text-muted">
                      {estate.address}, {estate.city} · {estate.county} County
                    </p>
                  </div>
                  <StatusBadge status={estate.status} />
                </div>
                <p className="mt-4 text-sm text-muted">
                  Last update {formatDate(estate.updates[0]?.createdAt || estate.updatedAt)}
                  {estate.updates[0] ? ` · ${estate.updates[0].body.slice(0, 90)}${estate.updates[0].body.length > 90 ? "…" : ""}` : ""}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Shell>
  );
}
