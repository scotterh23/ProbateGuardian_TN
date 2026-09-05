export const dynamic = "force-dynamic";

import Link from "next/link";
import { AttorneyImportForm } from "./ui";

export default function AttorneyImportPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-4 p-6">
      <div>
        <Link href="/attorneys" className="text-sm font-medium text-primary hover:underline">
          ← Attorneys board
        </Link>
        <h1 className="mt-2 text-2xl font-semibold">Import attorney contacts</h1>
        <p className="text-sm text-muted">
          Match on attorney UUID only. Non-empty firm / email / phone / county / address overwrite that field.
          Empty cells are ignored. Unknown ids are skipped — no attorneys are created. Leads are never written.
        </p>
      </div>
      <AttorneyImportForm />
    </div>
  );
}
