"use server";

import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import { outreachSummary } from "@/lib/lead-outreach";
import { loadLeads } from "@/lib/leads";

async function requireUser() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) throw new Error("Not signed in");
  return { supabase, user };
}

export async function signIn(email: string, password: string) {
  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) return { error: error.message };
  return { error: null };
}

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
}

export async function updateLeadStatus(leadId: string, status: string) {
  const { supabase } = await requireUser();
  const { error } = await supabase.from("leads").update({ status, updated_at: new Date().toISOString() }).eq("id", leadId);
  if (error) throw new Error(error.message);
  revalidatePath("/leads");
  revalidatePath(`/leads/${leadId}`);
}

export async function updateLeadNotes(leadId: string, notes: string) {
  const { supabase } = await requireUser();
  const { error } = await supabase
    .from("leads")
    .update({ notes, updated_at: new Date().toISOString() })
    .eq("id", leadId);
  if (error) throw new Error(error.message);
  revalidatePath("/leads");
  revalidatePath(`/leads/${leadId}`);
}

export async function updateFollowUpDate(leadId: string, followUpDate: string | null, currentStatus: string) {
  const { supabase } = await requireUser();
  const patch: Record<string, string | null> = {
    follow_up_date: followUpDate,
    updated_at: new Date().toISOString(),
  };
  if (followUpDate && (currentStatus === "new" || currentStatus === "contacted")) {
    patch.status = "follow_up";
  }
  const { error } = await supabase.from("leads").update(patch).eq("id", leadId);
  if (error) throw new Error(error.message);
  revalidatePath("/leads");
  revalidatePath(`/leads/${leadId}`);
}

export async function addActivity(leadId: string, type: "call" | "email" | "mailer", note?: string) {
  const { supabase, user } = await requireUser();
  const titles = { call: "Call logged", email: "Email logged", mailer: "Mailer logged" };
  const { error } = await supabase.from("lead_activities").insert({
    lead_id: leadId,
    type,
    activity_type: type,
    title: titles[type],
    content: note?.trim() || (type === "call" ? "Phone call made" : type === "email" ? "Email sent" : "Mailer sent"),
    created_by: user.id,
  });
  if (error) throw new Error(error.message);

  const { data: lead } = await supabase.from("leads").select("id, status").eq("id", leadId).maybeSingle();
  if (lead?.status === "new") {
    await supabase.from("leads").update({ status: "contacted", updated_at: new Date().toISOString() }).eq("id", leadId);
  }
  revalidatePath("/leads");
  revalidatePath(`/leads/${leadId}`);
}

export async function promoteNewLeadsWithCallHistory() {
  const { supabase } = await requireUser();
  const leads = await loadLeads({ status: "new", called: "oldest", due: "any", mailer: "any" });
  const ids = leads.filter((lead) => outreachSummary(lead).callCount > 0).map((lead) => lead.id);
  if (!ids.length) return { updated: 0 };
  const { error } = await supabase
    .from("leads")
    .update({ status: "contacted", updated_at: new Date().toISOString() })
    .in("id", ids)
    .eq("status", "new");
  if (error) throw new Error(error.message);
  revalidatePath("/leads");
  return { updated: ids.length };
}
