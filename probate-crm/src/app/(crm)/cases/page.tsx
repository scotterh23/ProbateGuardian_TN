import { createClient } from "@/lib/supabase/server";
import { BackToLeads, SimplePage } from "../simple-pages";

export default async function CasesPage() {
  const supabase = await createClient();
  const { data } = await supabase.from("cases").select("id, created_at").limit(20);
  return (
    <SimplePage title="Cases">
      <p className="text-sm text-muted">{data?.length ? `${data.length} cases on file.` : "No case files yet. Create one from a lead when you are ready."}</p>
      <BackToLeads />
    </SimplePage>
  );
}
