import { createClient } from "@/lib/supabase/server";
import { SimplePage } from "../simple-pages";

export default async function AttorneysPage() {
  const supabase = await createClient();
  const { data } = await supabase.from("attorneys").select("id, full_name").order("full_name").limit(100);
  return (
    <SimplePage title="Attorneys">
      <div className="space-y-2">
        {(data ?? []).map((row) => (
          <div key={row.id} className="rounded-lg border border-line bg-white p-3">
            {row.full_name}
          </div>
        ))}
      </div>
    </SimplePage>
  );
}
