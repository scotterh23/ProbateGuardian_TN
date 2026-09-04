import Link from "next/link";
import { loadLeads } from "@/lib/leads";
import { primaryContact } from "@/lib/types";
import { SimplePage } from "../simple-pages";

export default async function MailerQueuePage() {
  const leads = await loadLeads({ status: "call_list", called: "oldest", due: "any", mailer: "needs" });
  return (
    <SimplePage title="Mailer Queue">
      <p className="text-sm text-muted">{leads.length} leads need a mailer or have none logged yet.</p>
      <div className="space-y-2">
        {leads.slice(0, 80).map((lead) => {
          const contact = primaryContact(lead);
          return (
            <Link key={lead.id} href={`/leads/${lead.id}`} className="block rounded-lg border border-line bg-white p-3 hover:bg-slate-50">
              <span className="font-medium">{contact?.name || lead.decedent_name}</span>
              <span className="block text-xs text-muted">{lead.property_address || lead.notes_summary || "No address"}</span>
            </Link>
          );
        })}
      </div>
    </SimplePage>
  );
}
