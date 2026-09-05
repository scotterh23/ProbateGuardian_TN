"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import {
  ALL_STATUSES_FILTER,
  CALLED_NEVER,
  CALLED_NEWEST,
  CALLED_OLDEST,
  CALL_LIST_FILTER,
  DUE_ANY,
  DUE_FOLLOW_UP,
  DEFAULT_FILTERS,
  MAILER_ANY,
  MAILER_NEEDS,
  leadListHref,
  type LeadListFilters,
} from "@/lib/lead-filters";
import { persistLeadFilters, rememberOpenLead, saveLeadListScroll } from "@/lib/lead-memory";
import { formatDate, isFollowUpDueToday, isFollowUpOverdue } from "@/lib/dates";
import { outreachSummary } from "@/lib/lead-outreach";
import { LEAD_STATUSES, primaryContact, statusColor, statusLabel, type Lead } from "@/lib/types";
import { promoteNewLeadsWithCallHistory } from "./actions";

const QUICK = ["new", "contacted", "follow_up", "warm", "hot", "dnc"];

export function LeadListControls({ filters }: { filters: LeadListFilters }) {
  const router = useRouter();

  function apply(next: Partial<LeadListFilters>) {
    const merged = { ...filters, ...next };
    saveLeadListScroll();
    persistLeadFilters(merged);
    router.push(leadListHref(merged));
  }

  const dirty =
    filters.status !== DEFAULT_FILTERS.status ||
    filters.called !== DEFAULT_FILTERS.called ||
    filters.due !== DEFAULT_FILTERS.due ||
    filters.mailer !== DEFAULT_FILTERS.mailer;

  return (
    <div className="space-y-2 rounded-xl border border-line bg-white p-3">
      <div className="grid flex-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="space-y-1 text-sm">
          <span className="font-medium text-muted">Status</span>
          <select
            className="w-full rounded-md border border-line bg-white px-3 py-2"
            value={filters.status}
            onChange={(e) => apply({ status: e.target.value })}
          >
            <option value={CALL_LIST_FILTER}>Call list (hide DNC)</option>
            <option value={ALL_STATUSES_FILTER}>All statuses</option>
            {QUICK.map((value) => (
              <option key={value} value={value}>
                {LEAD_STATUSES.find((s) => s.value === value)?.label || value}
              </option>
            ))}
            {LEAD_STATUSES.filter((s) => !QUICK.includes(s.value)).map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-1 text-sm">
          <span className="font-medium text-muted">Last called</span>
          <select
            className="w-full rounded-md border border-line bg-white px-3 py-2"
            value={filters.called}
            onChange={(e) => apply({ called: e.target.value })}
            title="Never-called leads first. Then leads whose last logged call is oldest."
          >
            <option value={CALLED_OLDEST}>Never called first, then oldest last-called</option>
            <option value={CALLED_NEWEST}>Newest last-called first</option>
            <option value={CALLED_NEVER}>Never called only</option>
          </select>
          <p className="text-xs text-muted">
            Call order: people we have never called, then the longest time since a logged call. Status filters still apply on top of this.
          </p>
        </label>
        <label className="space-y-1 text-sm">
          <span className="font-medium text-muted">Mailer</span>
          <select
            className="w-full rounded-md border border-line bg-white px-3 py-2"
            value={filters.mailer}
            onChange={(e) => apply({ mailer: e.target.value })}
          >
            <option value={MAILER_ANY}>Any</option>
            <option value={MAILER_NEEDS}>Needs mailer (queue or none logged)</option>
          </select>
        </label>
        <label className="space-y-1 text-sm">
          <span className="font-medium text-muted">Follow-up</span>
          <select
            className="w-full rounded-md border border-line bg-white px-3 py-2"
            value={filters.due}
            onChange={(e) => apply({ due: e.target.value })}
          >
            <option value={DUE_ANY}>Any date</option>
            <option value={DUE_FOLLOW_UP}>Due today / overdue</option>
          </select>
        </label>
      </div>
      <form
        className="flex flex-wrap items-end gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          apply({ q: String(form.get("q") || "").trim() });
        }}
      >
        <label className="min-w-[220px] flex-1 space-y-1 text-sm">
          <span className="font-medium text-muted">Search (stacks with filters)</span>
          <input
            name="q"
            defaultValue={filters.q || ""}
            placeholder="Name, phone, case #, county…"
            className="w-full rounded-md border border-line bg-white px-3 py-2"
          />
        </label>
        <button type="submit" className="rounded-md border border-line bg-white px-3 py-2 text-sm">
          Search
        </button>
      </form>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-muted">
          Filters stack. Pick Needs Mailer and a last-called sort together. Email, call, and mailer are separate signals — a lead can have an email and still need a mailer.
        </p>
        {dirty || filters.q ? (
          <button type="button" className="text-xs font-semibold text-primary hover:underline" onClick={() => apply({ ...DEFAULT_FILTERS, q: "" })}>
            Reset filters
          </button>
        ) : null}
      </div>
    </div>
  );
}

export function LeadCard({ lead }: { lead: Lead }) {
  const contact = primaryContact(lead);
  const outreach = outreachSummary(lead);
  const property = lead.lead_properties?.[0];
  const address = property
    ? [property.address, property.city, property.state, property.zip].filter(Boolean).join(", ")
    : [lead.property_address, lead.property_city, lead.property_state, lead.property_zip].filter(Boolean).join(", ");

  return (
    <div id={`lead-card-${lead.id}`} className="group relative rounded-lg border border-line bg-white p-4 pr-12 shadow-sm hover:shadow-md">
      <Link
        href={`/leads/${lead.id}`}
        aria-label={`Open lead for ${contact?.name || lead.decedent_name}`}
        className="absolute inset-0 z-0 rounded-lg"
        onClick={() => {
          saveLeadListScroll(undefined, lead.id);
          rememberOpenLead(lead.id);
        }}
      />
      <div className="relative z-10 pointer-events-none">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-semibold text-slate-900">{contact?.name || lead.decedent_name || "Untitled lead"}</p>
            <p className="text-xs text-muted">
              {(contact?.relationship || "Executor").replace(/_/g, " ")}
              {contact?.is_primary ? " · Primary POC" : ""}
            </p>
            {contact?.phone ? (
              <p className="mt-1 text-sm text-primary">{contact.phone}</p>
            ) : (
              <p className="mt-1 text-sm font-medium text-amber-700">No phone on file — add in Contacts</p>
            )}
          </div>
          <span className={`rounded-full px-2.5 py-1 text-xs font-semibold text-white ${statusColor(lead.status)}`}>
            {statusLabel(lead.status)}
          </span>
        </div>
        <div className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-2 text-xs text-slate-600">
          <p>Re: {lead.decedent_name || "estate"}</p>
          <p>
            {lead.case_number ? `#${lead.case_number}` : "No case #"}
            {lead.county ? ` · ${lead.county}` : ""}
          </p>
          {address ? <p>{address}</p> : null}
          {lead.death_date ? <p>DOD: {formatDate(lead.death_date)}</p> : null}
        </div>
        <div className="mt-3 grid grid-cols-1 gap-1.5 text-xs text-muted sm:grid-cols-3">
          <span>📞 {outreach.callCount ? `${outreach.callCount} calls · ${formatDate(outreach.lastCalledAt) || "logged"}` : "Never called"}</span>
          <span>✉️ {outreach.emailCount ? `${outreach.emailCount} emails · ${formatDate(outreach.lastEmailAt) || "logged"}` : "0 emails — none"}</span>
          <span>📬 {outreach.mailerCount ? `${outreach.mailerCount} mailers · ${formatDate(outreach.lastMailerAt) || "logged"}` : "0 mailers — none"}</span>
        </div>
        {lead.follow_up_date ? (
          <p className={`mt-2 text-xs font-semibold ${isFollowUpOverdue(lead.follow_up_date) ? "text-amber-700" : "text-muted"}`}>
            Follow-up: {formatDate(lead.follow_up_date)}
            {isFollowUpOverdue(lead.follow_up_date) ? " · Overdue" : isFollowUpDueToday(lead.follow_up_date) ? " · Due today" : ""}
          </p>
        ) : null}
      </div>
    </div>
  );
}

export function PromoteSafeButton({ count }: { count: number }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [pending, start] = useTransition();
  const [error, setError] = useState<string | null>(null);
  if (!count) return null;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-md border border-line bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50"
      >
        Move {count} New lead{count === 1 ? "" : "s"} with a logged call to Contacted
      </button>
      {open ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
            <h2 className="text-lg font-semibold">Move New leads with a logged call to Contacted?</h2>
            <p className="mt-2 text-sm text-muted">
              This only changes leads that are still <strong>New</strong> and already have at least one logged call
              activity. It will not touch Warm, Hot, Follow-up, DNC, or Needs Mailer. Leads that are New with no
              logged call stay New.
            </p>
            <p className="mt-2 text-sm text-muted">
              Right now that is {count} lead{count === 1 ? "" : "s"}. Confirm only if Shelly wants those statuses
              updated.
            </p>
            {error ? <p className="mt-2 text-sm text-red-600">{error}</p> : null}
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="rounded-md px-3 py-2 text-sm" onClick={() => setOpen(false)}>
                Cancel
              </button>
              <button
                type="button"
                disabled={pending}
                className="rounded-md bg-primary px-3 py-2 text-sm text-white disabled:opacity-60"
                onClick={() => {
                  start(async () => {
                    try {
                      await promoteNewLeadsWithCallHistory();
                      setOpen(false);
                      router.refresh();
                    } catch (err) {
                      setError(err instanceof Error ? err.message : "Could not update leads");
                    }
                  });
                }}
              >
                {pending ? "Updating…" : `Update ${count}`}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
