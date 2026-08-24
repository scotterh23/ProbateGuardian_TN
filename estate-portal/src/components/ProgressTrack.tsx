import { EstateProgress } from "@prisma/client";
import { PROGRESS_HELP, PROGRESS_LABEL, PROGRESS_ORDER } from "@/lib/status";

export function ProgressTrack({ progress }: { progress: EstateProgress }) {
  const current = PROGRESS_ORDER.indexOf(progress);
  return (
    <ol className="space-y-4">
      {PROGRESS_ORDER.map((step, i) => {
        const done = i <= current;
        const active = i === current;
        return (
          <li key={step} className="flex gap-3">
            <span
              className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                done ? "bg-forest text-white" : "bg-mist text-muted"
              }`}
            >
              {i + 1}
            </span>
            <div>
              <p className={`text-sm font-semibold ${done ? "text-forest" : "text-muted"}`}>
                {PROGRESS_LABEL[step]}
                {active ? <span className="ml-2 text-xs font-medium text-accent">Current</span> : null}
              </p>
              <p className="mt-0.5 text-sm text-muted">{PROGRESS_HELP[step]}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
