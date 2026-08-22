import Link from "next/link";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { Shell } from "@/components/Shell";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate } from "@/lib/status";

export default async function AdminPage() {
  const session = await getSession();
  if (!session) redirect("/login");
  if (session.role !== "ADMIN") redirect("/dashboard");

  const estates = await prisma.estate.findMany({
    orderBy: { updatedAt: "desc" },
    include: { _count: { select: { members: true, documents: true, updates: true } } },
  });

  return (
    <Shell user={session}>
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-muted">Probate Guardians</p>
          <h1 className="font-serif text-3xl">Admin</h1>
          <p className="mt-1 text-muted">Create estates, invite people, and keep status current.</p>
        </div>
        <Link href="/admin/estates/new" className="rounded-xl bg-navy px-4 py-3 font-semibold text-white">
          Create estate
        </Link>
      </div>
      <ul className="grid gap-3">
        {estates.map((estate) => (
          <li key={estate.id} className="card flex flex-wrap items-center justify-between gap-3 p-4">
            <div>
              <Link href={`/estates/${estate.id}`} className="font-serif text-lg text-navy">
                {estate.nickname}
              </Link>
              <p className="text-sm text-muted">
                {estate.address}, {estate.city} · {estate._count.members} people ·{" "}
                {estate._count.updates} updates · last {formatDate(estate.updatedAt)}
              </p>
            </div>
            <StatusBadge status={estate.status} />
          </li>
        ))}
      </ul>
    </Shell>
  );
}
