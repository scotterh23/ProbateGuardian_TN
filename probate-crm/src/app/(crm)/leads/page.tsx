export const dynamic = "force-dynamic";

import { LeadListMemory } from "@/components/lead-list-memory";
import { parseLeadFilters } from "@/lib/lead-filters";
import { outreachSummary } from "@/lib/lead-outreach";
import { countSafeNewWithCalls, loadLeads } from "@/lib/leads";
import { LeadCard, LeadListControls, PromoteSafeButton } from "./ui";

export default async function LeadsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const filters = parseLeadFilters(params);
  const leads = await loadLeads(filters);
  const safeCount = filters.status === "new" ? leads.filter((lead) => outreachSummary(lead).callCount > 0).length : await countSafeNewWithCalls();

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <LeadListMemory filters={filters} />
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">All Leads</h1>
          <p className="text-sm text-muted">{leads.length} leads</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <PromoteSafeButton count={safeCount} />
        </div>
      </div>
      <LeadListControls filters={filters} />
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {leads.map((lead) => (
          <LeadCard key={lead.id} lead={lead} />
        ))}
      </div>
      {leads.length === 0 ? <p className="rounded-lg border border-dashed border-line p-8 text-center text-muted">No leads match these stacked filters.</p> : null}
    </div>
  );
}
