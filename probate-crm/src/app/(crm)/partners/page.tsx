import { createClient } from "@/lib/supabase/server";
import { SimplePage } from "../simple-pages";

export default async function PartnersPage() {
  const supabase = await createClient();
  const { data } = await supabase.from("partners").select("id").limit(20);
  return (
    <SimplePage title="Partners">
      <p className="text-sm text-muted">{data?.length ? `${data.length} partners.` : "No partners yet."}</p>
    </SimplePage>
  );
}
