"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { addActivity, updateFollowUpDate, updateLeadNotes, updateLeadStatus } from "@/app/(crm)/leads/actions";
import { formatDate, formatDateTime } from "@/lib/dates";
import { outreachSummary } from "@/lib/lead-outreach";
import { QUICK_STATUSES, activityKind, primaryContact, statusColor, statusLabel, type Lead } from "@/lib/types";

export function LeadStatusPills({ lead }: { lead: Lead }) {
  const router = useRouter();
  const [status, setStatus] = useState(lead.status);
  const [pending, start] = useTransition();

  function change(next: string) {
    if (next === status || pending) return;
    const prev = status;
    setStatus(next);
    start(async () => {
      try {
        await updateLeadStatus(lead.id, next);
        router.refresh();
      } catch {
        setStatus(prev);
      }
    });
  }

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
      <div className="flex flex-wrap items-center gap-1.5">
        {QUICK_STATUSES.map((value) => (
          <button
            key={value}
            type="button"
            disabled={pending}
            onClick={() => change(value)}
            className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${
              status === value ? `${statusColor(value)} border-transparent text-white` : "border-line bg-white text-slate-600"
            }`}
          >
            {statusLabel(value)}
          </button>
        ))}
      </div>
      <select
        className="rounded-md border border-line bg-white px-2 py-1 text-sm"
        value={status}
        disabled={pending}
        onChange={(e) => change(e.target.value)}
      >
        <option value={status}>{statusLabel(status)}</option>
        {status !== lead.status ? <option value={lead.status}>{statusLabel(lead.status)}</option> : null}
        {!QUICK_STATUSES.includes(status as (typeof QUICK_STATUSES)[number]) ? null : (
          <>
            <option value="needs_mailer">Needs Mailer</option>
            <option value="appointment_set">Appointment Set</option>
            <option value="under_contract">Under Contract</option>
            <option value="closed">Closed</option>
          </>
        )}
      </select>
      <span className={`w-fit rounded-full px-2.5 py-1 text-xs font-semibold text-white ${statusColor(status)}`}>{statusLabel(status)}</span>
    </div>
  );
}

export function OutreachPanel({ lead }: { lead: Lead }) {
  const router = useRouter();
  const [note, setNote] = useState("");
  const [pending, start] = useTransition();
  const outreach = outreachSummary(lead);
  const history = [...(lead.lead_activities ?? [])].sort((a, b) => b.created_at.localeCompare(a.created_at));

  function log(type: "call" | "email" | "mailer") {
    start(async () => {
      await addActivity(lead.id, type, note);
      setNote("");
      router.refresh();
    });
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Outreach</h2>
        <p className="text-sm text-muted">Calls, emails, and mailers on this executor — at a glance. Status stays its own field.</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-line bg-white p-4">
          <p className="text-xs font-semibold uppercase text-muted">Calls</p>
          <p className="mt-1 text-3xl font-semibold">{outreach.callCount}</p>
          <p className="text-sm text-muted">{outreach.lastCalledAt ? `Last ${formatDate(outreach.lastCalledAt)}` : "None yet"}</p>
        </div>
        <div className="rounded-lg border border-line bg-white p-4">
          <p className="text-xs font-semibold uppercase text-muted">Emails</p>
          <p className="mt-1 text-3xl font-semibold">{outreach.emailCount}</p>
          <p className="text-sm text-muted">{outreach.lastEmailAt ? `Last ${formatDate(outreach.lastEmailAt)}` : "None yet"}</p>
        </div>
        <div className="rounded-lg border border-line bg-white p-4">
          <p className="text-xs font-semibold uppercase text-muted">Mailers</p>
          <p className="mt-1 text-3xl font-semibold">{outreach.mailerCount}</p>
          <p className="text-sm text-muted">{outreach.lastMailerAt ? `Last ${formatDate(outreach.lastMailerAt)}` : "None yet"}</p>
        </div>
      </div>
      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Optional short note"
        className="w-full rounded-md border border-line p-3 text-sm"
        rows={2}
      />
      <div className="flex flex-wrap gap-2">
        <button type="button" disabled={pending} onClick={() => log("call")} className="rounded-md border border-line bg-white px-3 py-2 text-sm">
          Log call
        </button>
        <button type="button" disabled={pending} onClick={() => log("email")} className="rounded-md border border-line bg-white px-3 py-2 text-sm">
          Log email
        </button>
        <button type="button" disabled={pending} onClick={() => log("mailer")} className="rounded-md border border-line bg-white px-3 py-2 text-sm">
          Log mailer
        </button>
      </div>
      <div>
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted">History</h3>
        <div className="space-y-2">
          {history.length === 0 ? <p className="text-sm text-muted">No outreach logged yet.</p> : null}
          {history.map((item) => (
            <div key={item.id} className="rounded-md border border-line bg-white p-3 text-sm">
              <p className="font-medium capitalize">{activityKind(item) || "note"}</p>
              <p className="text-slate-700">{item.content || item.description || item.title}</p>
              <p className="text-xs text-muted">{formatDateTime(item.created_at)}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function FollowUpForm({ lead }: { lead: Lead }) {
  const router = useRouter();
  const [value, setValue] = useState(lead.follow_up_date?.slice(0, 10) ?? "");
  const [pending, start] = useTransition();

  return (
    <form
      className="rounded-lg border border-line bg-white p-4"
      onSubmit={(event) => {
        event.preventDefault();
        start(async () => {
          await updateFollowUpDate(lead.id, value || null, lead.status);
          router.refresh();
        });
      }}
    >
      <p className="font-medium">Follow-up date</p>
      <div className="mt-2 flex flex-wrap gap-2">
        <input type="date" value={value} onChange={(e) => setValue(e.target.value)} className="rounded-md border border-line px-3 py-2" />
        <button type="submit" disabled={pending} className="rounded-md bg-primary px-3 py-2 text-sm text-white">
          Save
        </button>
      </div>
      <p className="mt-2 text-xs text-muted">
        Saving a date sets status to Follow-up when the lead is New or Contacted. Warm, Hot, and DNC stay as they are. Current status: {statusLabel(lead.status)}.
      </p>
    </form>
  );
}

export function NotesForm({ lead }: { lead: Lead }) {
  const router = useRouter();
  const [value, setValue] = useState(lead.notes ?? "");
  const [pending, start] = useTransition();

  return (
    <form
      className="rounded-lg border border-line bg-white p-4"
      onSubmit={(event) => {
        event.preventDefault();
        start(async () => {
          await updateLeadNotes(lead.id, value);
          router.refresh();
        });
      }}
    >
      <p className="font-medium">Notes</p>
      <p className="mb-2 text-xs text-muted">Saved on this lead only. Status, calls, emails, and mailers stay separate.</p>
      <textarea value={value} onChange={(e) => setValue(e.target.value)} rows={4} className="w-full rounded-md border border-line p-3 text-sm" />
      <button type="submit" disabled={pending} className="mt-2 rounded-md bg-primary px-3 py-2 text-sm text-white">
        {pending ? "Saving…" : "Save notes"}
      </button>
    </form>
  );
}

export function ContactsPanel({ lead }: { lead: Lead }) {
  const contacts = lead.lead_contacts ?? [];
  return (
    <div className="rounded-lg border border-line bg-white p-4">
      <p className="font-medium">Contacts</p>
      {contacts.length === 0 ? <p className="mt-2 text-sm text-muted">No contacts on file.</p> : null}
      <div className="mt-2 space-y-2">
        {contacts.map((contact) => (
          <div key={contact.id} className="rounded-md border border-line p-3 text-sm">
            <p className="font-medium">
              {contact.name || "Unnamed"}
              {contact.is_primary ? <span className="ml-2 text-xs text-muted">Primary</span> : null}
            </p>
            <p className="text-muted">{(contact.relationship || "Executor").replace(/_/g, " ")}</p>
            {contact.phone ? <p className="text-primary">{contact.phone}</p> : <p className="text-amber-700">No phone</p>}
            {contact.email ? <p>{contact.email}</p> : null}
          </div>
        ))}
      </div>
    </div>
  );
}

export function LeadHeader({ lead }: { lead: Lead }) {
  const contact = primaryContact(lead);
  const property = lead.lead_properties?.[0];
  const address = property
    ? [property.address, property.city, property.state, property.zip].filter(Boolean).join(", ")
    : [lead.property_address, lead.property_city, lead.property_state, lead.property_zip].filter(Boolean).join(", ");

  return (
    <div className="space-y-2">
      <div>
        <h1 className="text-2xl font-semibold">{contact?.name || lead.decedent_name || "Lead"}</h1>
        <p className="text-sm text-muted">
          {(contact?.relationship || "Executor").replace(/_/g, " ")}
          {contact?.is_primary ? " · Primary POC" : ""}
        </p>
        {contact?.phone ? <p className="text-primary">{contact.phone}</p> : <p className="font-medium text-amber-700">No phone on file — add in Contacts</p>}
      </div>
      <div className="text-sm text-slate-600">
        <p>Re: {lead.decedent_name || "estate"}</p>
        <p>
          {lead.case_number ? `#${lead.case_number}` : "No case #"}
          {lead.county ? ` · ${lead.county} County` : ""}
        </p>
        {address ? <p>{address}</p> : null}
        {lead.death_date ? <p>DOD: {formatDate(lead.death_date)}</p> : null}
      </div>
    </div>
  );
}
