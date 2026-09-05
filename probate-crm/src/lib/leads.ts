import { createClient } from "@/lib/supabase/server";
import {
  ALL_STATUSES_FILTER,
  CALLED_NEVER,
  CALLED_NEWEST,
  CALL_LIST_FILTER,
  DUE_FOLLOW_UP,
  MAILER_NEEDS,
  type LeadListFilters,
} from "@/lib/lead-filters";
import { outreachSummary } from "@/lib/lead-outreach";
import { type Lead, type Profile } from "@/lib/types";
import { startOfToday } from "@/lib/dates";

export async function getProfile(): Promise<Profile | null> {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return null;
  const { data } = await supabase.from("profiles").select("id, email, full_name, role").eq("id", user.id).maybeSingle();
  return (
    data ?? {
      id: user.id,
      email: user.email ?? null,
      full_name: user.user_metadata?.full_name ?? user.email ?? null,
      role: "member",
    }
  );
}

function applyClientFilters(leads: Lead[], filters: LeadListFilters) {
  const today = startOfToday();
  return leads.filter((lead) => {
    if (filters.status === CALL_LIST_FILTER) {
      if (lead.status === "dnc") return false;
    } else if (filters.status !== ALL_STATUSES_FILTER) {
      if (lead.status !== filters.status) return false;
    }
    const outreach = outreachSummary(lead);
    if (filters.called === CALLED_NEVER && outreach.lastCalledAt) return false;
    if (filters.due === DUE_FOLLOW_UP) {
      if (!lead.follow_up_date) return false;
      const due = new Date(lead.follow_up_date);
      if (Number.isNaN(due.getTime()) || due > new Date(today.getTime() + 24 * 60 * 60 * 1000 - 1)) return false;
    }
    if (filters.mailer === MAILER_NEEDS && !outreach.needsMailer && outreach.mailerCount > 0) {
      return false;
    }
    if (filters.county && (lead.county || "").toLowerCase() !== filters.county.toLowerCase()) return false;
    if (filters.q) {
      const q = filters.q.toLowerCase();
      const blob = [
        lead.decedent_name,
        lead.case_number,
        lead.county,
        lead.property_address,
        ...(lead.lead_contacts ?? []).map((c) => `${c.name} ${c.phone} ${c.email}`),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      if (!blob.includes(q)) return false;
    }
    return true;
  });
}

function sortLeads(leads: Lead[], called: string) {
  const withKey = leads.map((lead) => {
    const lastCalled = outreachSummary(lead).lastCalledAt;
    return { lead, lastCalled };
  });
  withKey.sort((a, b) => {
    if (called === CALLED_NEWEST) {
      if (!a.lastCalled && !b.lastCalled) return (b.lead.created_at || "").localeCompare(a.lead.created_at || "");
      if (!a.lastCalled) return 1;
      if (!b.lastCalled) return -1;
      return b.lastCalled.localeCompare(a.lastCalled);
    }
    // oldest / never: never-called first, then oldest last-called
    if (!a.lastCalled && !b.lastCalled) return (a.lead.created_at || "").localeCompare(b.lead.created_at || "");
    if (!a.lastCalled) return -1;
    if (!b.lastCalled) return 1;
    return a.lastCalled.localeCompare(b.lastCalled);
  });
  return withKey.map((row) => row.lead);
}

export async function loadLeads(filters: LeadListFilters): Promise<Lead[]> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("leads")
    .select("*, lead_contacts(*), lead_properties(*), lead_activities(*)")
    .order("created_at", { ascending: false });
  if (error) throw error;
  const leads = (data ?? []) as Lead[];
  return sortLeads(applyClientFilters(leads, filters), filters.called);
}

export async function loadLead(id: string): Promise<Lead | null> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("leads")
    .select("*, lead_contacts(*), lead_properties(*), lead_activities(*)")
    .eq("id", id)
    .maybeSingle();
  if (error) throw error;
  return (data as Lead | null) ?? null;
}

export async function countSafeNewWithCalls() {
  const leads = await loadLeads({
    status: "new",
    called: "oldest",
    due: "any",
    mailer: "any",
  });
  return leads.filter((lead) => outreachSummary(lead).callCount > 0).length;
}
