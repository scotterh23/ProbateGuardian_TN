import { createClient } from "@/lib/supabase/server";
import { isAttorneyId } from "@/lib/attorney-contact";
import type { Attorney } from "@/lib/types";

export async function loadAttorneys(): Promise<Attorney[]> {
  const supabase = await createClient();
  const { data, error } = await supabase.from("attorneys").select("*").order("full_name", { ascending: true });
  if (error) throw error;
  return (data ?? []) as Attorney[];
}

export async function loadAttorney(id: string): Promise<Attorney | null> {
  if (!isAttorneyId(id)) return null;
  const supabase = await createClient();
  const { data, error } = await supabase.from("attorneys").select("*").eq("id", id).maybeSingle();
  if (error) throw error;
  return (data as Attorney | null) ?? null;
}
