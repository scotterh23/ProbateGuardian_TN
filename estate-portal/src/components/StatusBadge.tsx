import { EstateStatus } from "@prisma/client";
import { STATUS_LABEL } from "@/lib/status";

const TONE: Record<EstateStatus, string> = {
  LETTERS: "bg-mist text-navy",
  VALUATION: "bg-accent-soft text-accent",
  LISTED: "bg-sky-50 text-sky-800",
  UNDER_CONTRACT: "bg-amber-50 text-amber-800",
  CLOSED: "bg-emerald-50 text-emerald-800",
};

export function StatusBadge({ status }: { status: EstateStatus }) {
  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold tracking-wide ${TONE[status]}`}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}
