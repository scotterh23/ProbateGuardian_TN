export const dynamic = "force-dynamic";

import { notFound } from "next/navigation";
import { LeadBackLink } from "@/components/lead-back-link";
import { loadLead } from "@/lib/leads";
import { ContactsPanel, FollowUpForm, LeadHeader, LeadStatusPills, NotesForm, OutreachPanel } from "./ui";

export default async function LeadDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const lead = await loadLead(id);
  if (!lead) notFound();

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div className="flex items-start gap-3">
        <LeadBackLink />
        <LeadHeader lead={lead} />
      </div>
      <LeadStatusPills lead={lead} />
      <OutreachPanel lead={lead} />
      <div className="grid gap-4 md:grid-cols-2">
        <FollowUpForm lead={lead} />
        <NotesForm lead={lead} />
      </div>
      <ContactsPanel lead={lead} />
    </div>
  );
}
