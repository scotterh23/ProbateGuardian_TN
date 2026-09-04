import { createClient } from "@/lib/supabase/server";
import { BackToLeads, SimplePage } from "../simple-pages";

export default async function DashboardPage() {
  const supabase = await createClient();
  const { count: total } = await supabase.from("leads").select("id", { count: "exact", head: true });
  const { count: fresh } = await supabase.from("leads").select("id", { count: "exact", head: true }).eq("status", "new");
  const { count: mailer } = await supabase.from("leads").select("id", { count: "exact", head: true }).eq("status", "needs_mailer");
  const { count: contacted } = await supabase.from("leads").select("id", { count: "exact", head: true }).eq("status", "contacted");

  return (
    <SimplePage title="Dashboard">
      <div className="grid gap-3 sm:grid-cols-4">
        {[
          ["All leads", total ?? 0],
          ["New", fresh ?? 0],
          ["Contacted", contacted ?? 0],
          ["Needs Mailer", mailer ?? 0],
        ].map(([label, value]) => (
          <div key={String(label)} className="rounded-lg border border-line bg-white p-4">
            <p className="text-xs uppercase text-muted">{label}</p>
            <p className="mt-1 text-3xl font-semibold">{value}</p>
          </div>
        ))}
      </div>
      <BackToLeads />
    </SimplePage>
  );
}
