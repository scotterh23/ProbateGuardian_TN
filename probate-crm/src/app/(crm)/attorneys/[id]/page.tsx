export const dynamic = "force-dynamic";

import Link from "next/link";
import { notFound } from "next/navigation";
import { loadAttorney } from "@/lib/attorneys";
import { AttorneyContactForm } from "./ui";

export default async function AttorneyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const attorney = await loadAttorney(id);
  if (!attorney) notFound();

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <div>
        <Link href="/attorneys" className="text-sm font-medium text-primary hover:underline">
          ← Attorneys board
        </Link>
        <h1 className="mt-2 text-2xl font-semibold">{attorney.full_name || "Attorney"}</h1>
        <p className="text-sm text-muted">
          Contact on this attorney row only. Saving never writes lead records.
        </p>
      </div>
      <AttorneyContactForm attorney={attorney} />
    </div>
  );
}
