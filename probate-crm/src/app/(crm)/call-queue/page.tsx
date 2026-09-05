import Link from "next/link";
import { formatDate } from "@/lib/dates";
import { loadLeads } from "@/lib/leads";
import { outreachSummary } from "@/lib/lead-outreach";
import { primaryContact } from "@/lib/types";
import { SimplePage } from "../simple-pages";

export default async function CallQueuePage() {
  const leads = (await loadLeads({ status: "call_list", called: "oldest", due: "any", mailer: "any" })).slice(0, 40);
  return (
    <SimplePage title="Call Queue">
      <p className="text-sm text-muted">Never-called first, then oldest last-called. Same order as the Leads list default.</p>
      <div className="space-y-2">
        {leads.map((lead) => {
          const contact = primaryContact(lead);
          const outreach = outreachSummary(lead);
          return (
            <Link key={lead.id} href={`/leads/${lead.id}`} className="block rounded-lg border border-line bg-white p-3 hover:bg-slate-50">
              <span className="font-medium">{contact?.name || lead.decedent_name}</span>
              <span className="ml-2 text-sm text-muted">{contact?.phone || "No phone"}</span>
              <span className="block text-xs text-muted">{outreach.lastCalledAt ? `Last called ${formatDate(outreach.lastCalledAt)}` : "Never called"}</span>
            </Link>
          );
        })}
      </div>
    </SimplePage>
  );
}
