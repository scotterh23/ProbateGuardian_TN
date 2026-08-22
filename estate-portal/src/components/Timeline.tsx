import { EstateStatus } from "@prisma/client";
import { STATUS_LABEL, STATUS_ORDER } from "@/lib/status";

export function Timeline({ status }: { status: EstateStatus }) {
  const current = STATUS_ORDER.indexOf(status);
  return (
    <ol className="grid grid-cols-1 gap-3 sm:grid-cols-5">
      {STATUS_ORDER.map((step, i) => {
        const done = i <= current;
        return (
          <li key={step} className="flex items-center gap-3 sm:block">
            <span
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                done ? "bg-navy text-white" : "bg-mist text-muted"
              }`}
            >
              {i + 1}
            </span>
            <span className={`text-sm ${done ? "text-navy" : "text-muted"}`}>
              {STATUS_LABEL[step]}
            </span>
            {i < STATUS_ORDER.length - 1 && (
              <span className="ml-4 hidden h-px flex-1 bg-line sm:mt-3 sm:block" />
            )}
          </li>
        );
      })}
    </ol>
  );
}
