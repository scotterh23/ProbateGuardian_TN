import { createClient } from "@/lib/supabase/server";
import { SimplePage } from "../simple-pages";

export default async function AgentsPage() {
  const supabase = await createClient();
  const { data } = await supabase.from("profiles").select("id, full_name, email, role").order("full_name");
  return (
    <SimplePage title="Agents">
      <div className="space-y-2">
        {(data ?? []).map((row) => (
          <div key={row.id} className="rounded-lg border border-line bg-white p-3">
            <p className="font-medium">{row.full_name || row.email}</p>
            <p className="text-xs text-muted">
              {row.email} · {row.role}
            </p>
          </div>
        ))}
      </div>
    </SimplePage>
  );
}
