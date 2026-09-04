import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { LEAD_STATUSES, statusColor, statusLabel } from "@/lib/types";
import { SimplePage } from "../simple-pages";

export default async function PipelinePage() {
  const supabase = await createClient();
  const { data } = await supabase.from("leads").select("id, decedent_name, status").order("updated_at", { ascending: false });
  const groups = LEAD_STATUSES.map((status) => ({
    ...status,
    leads: (data ?? []).filter((lead) => lead.status === status.value).slice(0, 12),
  })).filter((group) => group.leads.length);

  return (
    <SimplePage title="Pipeline">
      <div className="flex gap-3 overflow-x-auto pb-4">
        {groups.map((group) => (
          <section key={group.value} className="w-64 shrink-0 rounded-lg border border-line bg-white p-3">
            <h2 className="mb-2 flex items-center justify-between text-sm font-semibold">
              {group.label}
              <span className={`rounded-full px-2 py-0.5 text-xs text-white ${statusColor(group.value)}`}>{group.leads.length}</span>
            </h2>
            <div className="space-y-2">
              {group.leads.map((lead) => (
                <Link key={lead.id} href={`/leads/${lead.id}`} className="block rounded-md border border-line p-2 text-sm hover:bg-slate-50">
                  {lead.decedent_name || "Lead"}
                  <span className="block text-xs text-muted">{statusLabel(lead.status)}</span>
                </Link>
              ))}
            </div>
          </section>
        ))}
      </div>
    </SimplePage>
  );
}
