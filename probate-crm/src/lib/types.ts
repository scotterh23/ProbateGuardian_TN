export const LEAD_STATUSES = [
  { value: "new", label: "New", color: "bg-sky-600" },
  { value: "contacted", label: "Contacted", color: "bg-slate-500" },
  { value: "follow_up", label: "Follow Up", color: "bg-yellow-500" },
  { value: "warm", label: "Warm", color: "bg-orange-500" },
  { value: "hot", label: "Hot", color: "bg-red-500" },
  { value: "dnc", label: "DNC", color: "bg-zinc-700" },
  { value: "appointment_set", label: "Appointment Set", color: "bg-blue-500" },
  { value: "under_contract", label: "Under Contract", color: "bg-purple-500" },
  { value: "closed", label: "Closed", color: "bg-green-500" },
  { value: "no_interest", label: "No Interest", color: "bg-gray-500" },
  { value: "needs_mailer", label: "Needs Mailer", color: "bg-teal-600" },
  { value: "invalid_phone", label: "Invalid Phone", color: "bg-rose-600" },
] as const;

export type LeadStatus = (typeof LEAD_STATUSES)[number]["value"];

export const QUICK_STATUSES = ["new", "contacted", "follow_up", "warm", "hot", "dnc"] as const;

export type LeadContact = {
  id: string;
  lead_id: string;
  name: string | null;
  relationship: string | null;
  phone: string | null;
  email: string | null;
  is_primary: boolean | null;
  notes: string | null;
  address: string | null;
};

export type LeadProperty = {
  id: string;
  lead_id: string;
  address: string | null;
  city: string | null;
  state: string | null;
  zip: string | null;
};

export type LeadActivity = {
  id: string;
  lead_id: string;
  type: string | null;
  activity_type: string | null;
  title: string | null;
  content: string | null;
  description: string | null;
  created_at: string;
};

export type Lead = {
  id: string;
  decedent_name: string | null;
  case_number: string | null;
  county: string | null;
  death_date: string | null;
  property_address: string | null;
  property_city: string | null;
  property_state: string | null;
  property_zip: string | null;
  status: string;
  notes: string | null;
  notes_summary: string | null;
  follow_up_date: string | null;
  created_at: string;
  updated_at: string | null;
  lead_contacts?: LeadContact[];
  lead_properties?: LeadProperty[];
  lead_activities?: LeadActivity[];
};

export type Profile = {
  id: string;
  email: string | null;
  full_name: string | null;
  role: string | null;
};

export function statusLabel(status: string) {
  return LEAD_STATUSES.find((s) => s.value === status)?.label ?? status;
}

export function statusColor(status: string) {
  return LEAD_STATUSES.find((s) => s.value === status)?.color ?? "bg-slate-500";
}

export function activityKind(activity: LeadActivity) {
  return (activity.type || activity.activity_type || "").toLowerCase();
}

export function primaryContact(lead: Lead): LeadContact | undefined {
  const contacts = lead.lead_contacts ?? [];
  return contacts.find((c) => c.is_primary) ?? contacts[0];
}
